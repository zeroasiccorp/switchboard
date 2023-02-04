#ifndef __UMISB_HPP__
#define __UMISB_HPP__

#include <memory>
#include <sstream>
#include <iostream>

#include "switchboard.hpp"
#include "umilib.hpp"

// generic formatting methods

template <typename T> std::string umi_data_as_str(T& x) {
    // get the data representation
    uint8_t* ptr = x.ptr();
    size_t len = x.len();

    // create a formatted representation
    std::stringstream stream;
    stream << "[";
    for (int i=0; i<len; i++) {
        stream << "0x" << std::hex << ptr[i];
        if (i != (len-1)){
            stream << ", ";
        }
    }
    stream << "]";

    // return the result
    return stream.str();
}

template <typename T> std::string umi_transaction_as_str(T& x) {
    std::stringstream stream;
    stream << "opcode: " << umi_opcode_to_str(x.opcode) << std::endl;
    stream << "size: " << x.size << std::endl;
    stream << "user: " << x.user << std::endl;
    stream << "dstaddr: 0x" << std::hex << x.dstaddr << std::endl;
    stream << "srcaddr: 0x" << std::hex << x.srcaddr << std::endl;
    stream << "data: " << umi_data_as_str<T>(x);
    return stream.str();
}

// function for checking if requests and replies match up as expected

template <typename T> void umisb_check_reply(T& request, T& reply) {
    // check that the response makes sense
    if (!is_umi_write_response(reply.opcode)) {
        std::cerr << "Warning: got " << umi_opcode_to_str(reply.opcode)
            << " in response to " << umi_opcode_to_str(request.opcode)
            << " (expected WRITE-RESPONSE)" << std::endl;
    }
    if (reply.size != request.size) {
        std::cerr << "Warning: " << umi_opcode_to_str(request.opcode)
            << " response size is " << std::to_string(reply.size)
            << " (expected " << std::to_string(request.size) << ")" << std::endl;
    }
    if (reply.dstaddr != request.srcaddr) {
        std::cerr <<  "Warning: dstaddr in " << umi_opcode_to_str(request.opcode)
            << " response is " << std::to_string(reply.dstaddr)
            << " (expected " << std::to_string(request.srcaddr) << ")" << std::endl;
    }
}

// basic class for representing a UMI transaction, which may span
// multiple packets.

struct UmiTransaction {
    UmiTransaction(uint32_t opcode=0, uint32_t size=0, uint32_t user=0, uint64_t dstaddr=0,
        uint64_t srcaddr=0, uint8_t* data=NULL, size_t nbytes=0) : opcode(opcode), size(size),
        user(user), dstaddr(dstaddr), srcaddr(srcaddr), data(data), nbytes(nbytes),
        allocated(false) {

        if ((data == NULL) && (nbytes > 0)) {
            resize(nbytes);
        }

    }

    ~UmiTransaction() {
        if (allocated) {
            delete[] data;
        }
    }

    std::string toString() {
        return umi_transaction_as_str<UmiTransaction>(*this);
    }

    void resize(size_t n) {
        // allocate new space if needed
        if (n > nbytes) {
            if (allocated) {
                delete[] data;
            }
            data = new uint8_t[n];
            allocated = true;
        }

        // record the new size of the storage
        nbytes = n;
    }

    size_t len(){
        return nbytes;
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
        size_t nbytes;
        bool allocated;
};

// higher-level functions for UMI transactions

template <typename T> static inline bool umisb_send(
    T& x, SBTX& tx, bool blocking=true, void (*loop)(void)=NULL) {

    // sends (or tries to send, if blocking=false) a single UMI transaction
    // if length of the data payload in the packet is greater than
    // what can be sent in a header packet, then a header packet is sent
    // containing the beginning of the data, followed by the rest in
    // subsequent burst packets.

    if (!tx.is_active()) {
        return false;
    }

    // calculate the number of data bytes in the first packet

    int nbytes = x.len();
    size_t flit_size = std::min(nbytes, 16);

    // format into a UMI packet

    sb_packet p;
    uint8_t* ptr = x.ptr();
    umi_pack((uint32_t*)p.data, x.opcode, x.size, x.user, x.dstaddr,
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

    // update indices
    nbytes -= flit_size;
    ptr += flit_size;

    // send the remaining data in burst packets as necessary
    while (nbytes > 0) {
        // format the next burst packet
        flit_size = std::min(nbytes, 32);
        umi_pack_burst((uint32_t*)p.data, ptr, flit_size);

        // send the packet
        while (!tx.send(p)) {
            if (loop) {
                loop();
            }
        }

        // update indices
        nbytes -= flit_size;
        ptr += flit_size;
    }

    // if we reach this point, we succeeded in sending the packet
    return true;
} 

template <typename T> static inline bool umisb_recv(
    T& x, SBRX& rx, bool blocking=true, void (*loop)(void)=NULL) {

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
    umi_unpack((uint32_t*)p.data, x.opcode, x.size, x.user, x.dstaddr, x.srcaddr, NULL, 0);

    // determine how many bytes are in the payload

    int nbytes = is_umi_read_request(x.opcode) ? 0 : (1<<x.size);

    // create an object to hold data to be returned to python

    x.resize(nbytes);

    // initialize indices

    uint8_t* ptr = x.ptr();

    // calculate how many bytes are in the first (and possibly only) flit

    size_t flit_size = std::min(nbytes, 16);

    // copy out the data from the header packet

    copy_umi_data((uint32_t*)p.data, ptr, flit_size);

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

        // calculate how many bytes will be in this flit

        flit_size = std::min(nbytes, 32);
        
        // unpack data from the flit

        umi_unpack_burst((uint32_t*)p.data, ptr, flit_size);

        // update indices

        nbytes -= flit_size;
        ptr += flit_size;
    }

    return true;
}

#endif // __UMISB_HPP__
