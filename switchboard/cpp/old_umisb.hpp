#ifndef __OLD_UMISB_HPP__
#define __OLD_UMISB_HPP__

#include <memory>
#include <sstream>
#include <iostream>
#include <functional>

#include "switchboard.hpp"
#include "old_umilib.hpp"

typedef std::function<void(sb_packet packet, bool header)> PacketPrinter;

// generic formatting methods

template <typename T> std::string old_umi_data_as_str(T& x, ssize_t max_len=-1) {
    // get the data representation
    uint8_t* ptr = x.ptr();
    size_t len = x.nbytes();

    // if max_len is provided (non-negative), then it limits the amount
    // of data printed out.  the main use case is setting max_len=1<<size,
    // so that if the data buffer is larger than necessary, only valid
    // data gets printed out.
    if (max_len >= 0) {
        len = std::min(len, (size_t)max_len);
    }

    // create a formatted representation
    std::stringstream stream;
    stream << "[";
    for (size_t i=0; i<len; i++) {
        // uint8_t needs to be cast to an integer to print correctly
        // with std::hex: https://stackoverflow.com/a/23575509
        stream << "0x" << std::hex << static_cast<int>(ptr[i]);
        if (i != (len-1)){
            stream << ", ";
        }
    }
    stream << "]";

    // return the result
    return stream.str();
}

template <typename T> std::string old_umi_transaction_as_str(T& x) {
    std::stringstream stream;

    stream << "opcode: " << old_umi_opcode_to_str(x.opcode);

    stream << std::endl << "size: " << x.size;
    stream << std::endl << "user: " << x.user;
    stream << std::endl << "dstaddr: 0x" << std::hex << x.dstaddr;

    // print out the source address, as long as this isn't a write,
    // since a write doesn't have a source address
    if (!old_is_umi_write(x.opcode)) {
        stream << std::endl << "srcaddr: 0x" << std::hex << x.srcaddr;
    }

    // print out the data as long as this isn't a read request, since
    // that doesn't have data
    if (!old_is_umi_read_request(x.opcode)) {
        stream << std::endl << "data: " << old_umi_data_as_str<T>(x, 1<<x.size);
    }

    // return the result, noting that it does not contain a final newline
    return stream.str();
}

// function for checking if requests and replies match up as expected

template <typename T> void old_umisb_check_reply(T& request, T& reply) {
    // check that the response makes sense
    if (!old_is_umi_write_response(reply.opcode)) {
        std::cerr << "Warning: got " << old_umi_opcode_to_str(reply.opcode)
            << " in response to " << old_umi_opcode_to_str(request.opcode)
            << " (expected WRITE-RESPONSE)" << std::endl;
    }
    if (reply.size != request.size) {
        std::cerr << "Warning: " << old_umi_opcode_to_str(request.opcode)
            << " response size is " << std::to_string(reply.size)
            << " (expected " << std::to_string(request.size) << ")" << std::endl;
    }
    if (reply.dstaddr != request.srcaddr) {
        std::cerr <<  "Warning: dstaddr in " << old_umi_opcode_to_str(request.opcode)
            << " response is " << std::to_string(reply.dstaddr)
            << " (expected " << std::to_string(request.srcaddr) << ")" << std::endl;
    }
}

// basic class for representing a UMI transaction, which may span
// multiple packets.

struct OldUmiTransaction {
    OldUmiTransaction(uint32_t opcode=0, uint32_t size=0, uint32_t user=0, uint64_t dstaddr=0,
        uint64_t srcaddr=0, uint8_t* data=NULL, size_t nbytes=0) : opcode(opcode), size(size),
        user(user), dstaddr(dstaddr), srcaddr(srcaddr), data(data), m_nbytes(nbytes),
        allocated(false) {

        if ((data == NULL) && (nbytes > 0)) {
            resize(nbytes);
        }

    }

    ~OldUmiTransaction() {
        if (allocated) {
            delete[] data;
        }
    }

    std::string toString() {
        return old_umi_transaction_as_str<OldUmiTransaction>(*this);
    }

    void resize(size_t n) {
        // allocate new space if needed
        if (n > m_nbytes) {
            if (allocated) {
                delete[] data;
            }
            data = new uint8_t[n];
            allocated = true;
        }

        // record the new size of the storage
        m_nbytes = n;
    }

    size_t nbytes(){
        return m_nbytes;
    }

    uint8_t* ptr() {
        return data;
    }

    uint32_t opcode;
    uint32_t size;
    uint32_t user;
    uint64_t dstaddr;
    uint64_t srcaddr;
    uint8_t* data;

    private:
        size_t m_nbytes;
        bool allocated;
};

// higher-level functions for UMI transactions

template <typename T> static inline bool old_umisb_send(
    T& x, SBTX& tx, bool blocking=true, void (*loop)(void)=NULL,
    PacketPrinter printer=NULL) {

    // sends (or tries to send, if blocking=false) a single UMI transaction
    // if length of the data payload in the packet is greater than
    // what can be sent in a header packet, then a header packet is sent
    // containing the beginning of the data, followed by the rest in
    // subsequent burst packets.

    if (!tx.is_active()) {
        return false;
    }

    // calculate the number of data bytes in the first packet

    int nbytes = x.nbytes();
    size_t flit_size = std::min(nbytes, 16);

    // format into a UMI packet

    sb_packet p;
    uint8_t* ptr = x.ptr();
    old_umi_pack((uint32_t*)p.data, x.opcode, x.size, x.user, x.dstaddr,
        x.srcaddr, ptr, flit_size);

    // try to send the packet once or multiple times depending
    // on the "blocking" argument

    bool header_sent = tx.send(p);
    if ((!blocking) && (!header_sent)) {
        return false;
    }

    // if we reach this point, we're committed to send out the whole UMI
    // transaction, which may span multiple packet

    // finish sending the header packet
    if (!header_sent) {
        while (!tx.send(p)) {
            if (loop) {
                loop();
            }
        }
    }
    if (printer != NULL)
        printer(p, true);

    // update indices
    nbytes -= flit_size;
    ptr += flit_size;

    // send the remaining data in burst packets as necessary
    while (nbytes > 0) {
        // format the next burst packet
        flit_size = std::min(nbytes, 32);
        old_umi_pack_burst((uint32_t*)p.data, ptr, flit_size);

        // send the packet
        while (!tx.send(p)) {
            if (loop) {
                loop();
            }
        }
        if (printer != NULL)
            printer(p, false);

        // update indices
        nbytes -= flit_size;
        ptr += flit_size;
    }

    // if we reach this point, we succeeded in sending the packet
    return true;
}

template <typename T> static inline bool old_umisb_recv(
    T& x, SBRX& rx, bool blocking=true, void (*loop)(void)=NULL, PacketPrinter printer=NULL) {

    // if the receive side isn't active, there is nothing to receive
    if (!rx.is_active()) {
        return false;
    }

    // get a resposne

    sb_packet p;

    if (!blocking) {
        if (!rx.recv(p)) {
            return false;
        }
    } else {
        while (!rx.recv(p)) {
            if (loop) {
                loop();
            }
        }
    }

    // if we get to this point, there is valid data in "p"

    // parse the packet (but don't copy out the data, since we don't yet
    // know how much space to allocate to hold it)
    old_umi_unpack((uint32_t*)p.data, x.opcode, x.size, x.user, x.dstaddr, x.srcaddr, NULL, 0);

    if (printer != NULL)
        printer(p, true);

    // determine how many bytes are in the payload

    int nbytes = old_is_umi_read_request(x.opcode) ? 0 : (1<<x.size);

    // create an object to hold data to be returned to python

    x.resize(nbytes);

    // initialize indices

    uint8_t* ptr = x.ptr();

    // calculate how many bytes are in the first (and possibly only) flit

    size_t flit_size = std::min(nbytes, 16);

    // copy out the data from the header packet

    old_copy_umi_data((uint32_t*)p.data, ptr, flit_size);

    // update indices

    nbytes -= flit_size;
    ptr += flit_size;

    // receive more data if necessary

    while (nbytes > 0) {
        // receive the next packet

        while (!rx.recv(p)) {
            if (loop) {
                loop();
            }
        }
        if (printer != NULL)
            printer(p, false);

        // calculate how many bytes will be in this flit

        flit_size = std::min(nbytes, 32);

        // unpack data from the flit

        old_umi_unpack_burst((uint32_t*)p.data, ptr, flit_size);

        // update indices

        nbytes -= flit_size;
        ptr += flit_size;
    }

    return true;
}

#endif // __OLD_UMISB_HPP__
