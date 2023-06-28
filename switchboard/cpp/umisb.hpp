#ifndef __UMISB_HPP__
#define __UMISB_HPP__

#include <memory>
#include <sstream>
#include <iostream>
#include <functional>

#include "switchboard.hpp"
#include "umilib.h"
#include "umilib.hpp"

typedef std::function<void(sb_packet packet, bool header)> PacketPrinter;

// generic formatting methods

template <typename T> std::string umi_data_as_str(T& x) {
    // get the data representation
    uint8_t* ptr = x.ptr();
    size_t nbytes = x.nbytes();

    uint32_t opcode = umi_opcode(x.cmd);

    // create a formatted representation
    std::stringstream stream;
    stream << "[";
    if (has_umi_data(opcode)) {

        uint32_t size = umi_size(x.cmd);
        uint32_t len = umi_len(x.cmd)+1;

        for (size_t i=0; i<len; i++) {
            if ((i+1)*(1<<size) <= nbytes) {
                if (size == 0) {
                    // uint8_t needs to be cast to an integer to print correctly
                    // with std::hex: https://stackoverflow.com/a/23575509
                    stream << "0x" << std::hex << static_cast<int>(ptr[i]);
                } else if (size == 1) {
                    stream << "0x" << std::hex << ((uint16_t*)ptr)[i];
                } else if (size == 2) {
                    stream << "0x" << std::hex << ((uint32_t*)ptr)[i];
                } else if (size == 3) {
                    stream << "0x" << std::hex << ((uint64_t*)ptr)[i];
                } else {
                    stream << "X";
                }
            } else {
                stream << "X";
            }
            if (i != (len-1)){
                stream << ", ";
            }
        }
    }

    stream << "]";

    // return the result
    return stream.str();
}

template <typename T> std::string umi_transaction_as_str(T& x) {
    std::stringstream stream;

    uint32_t opcode = umi_opcode(x.cmd);

    stream << "opcode: " << umi_opcode_to_str(opcode);

    stream << std::endl << "dstaddr: 0x" << std::hex << x.dstaddr;
    
    // print out the source address if this is a request, as long
    // as it isn't a posted write, since that doesn't have a source
    // address.
    if (is_umi_req(opcode) && (opcode != UMI_REQ_POSTED)) {
        stream << std::endl << "srcaddr: 0x" << std::hex << x.srcaddr;
    }

    // print out the data as long as this isn't a read request, since
    // that doesn't have data
    if (opcode != UMI_REQ_READ) {
        stream << std::endl << "data: " << umi_data_as_str<T>(x);
    }

    // return the result, noting that it does not contain a final newline
    return stream.str();
}

// function for checking if requests and replies match up as expected

template <typename T> void umisb_check_resp(T& req, T& resp) {
    uint32_t req_opcode = umi_opcode(req.cmd);

    if (!has_umi_resp(req_opcode)) {
        return;
    }

    uint32_t req_size = umi_size(req.cmd);
    uint32_t req_len = umi_len(req.cmd);

    uint32_t resp_opcode = umi_opcode(resp.cmd);
    uint32_t resp_size = umi_size(req.cmd);
    uint32_t resp_len = umi_len(req.cmd);

    uint32_t expected_opcode;
    uint32_t expected_size = umi_size(req.cmd);    
    uint32_t expected_len = umi_len(req.cmd);
    uint64_t expected_dstaddr = req.srcaddr;

    if (req_opcode == UMI_REQ_WRITE) {
        expected_opcode = UMI_RESP_WRITE;
    } else if (req_opcode == UMI_REQ_READ) {
        expected_opcode = UMI_RESP_READ;
    } else if (req_opcode == UMI_REQ_ATOMIC) {
        expected_opcode = UMI_RESP_READ;  // TODO: is this right?
    }

    // check that the response makes sense

    if (resp_opcode != expected_opcode) {
        std::cerr << "Warning: got " << umi_opcode_to_str(resp_opcode)
            << " in response to " << umi_opcode_to_str(req_opcode)
            << " (expected " << umi_opcode_to_str(expected_opcode)
            << ")" << std::endl;
    }

    if (resp_size != expected_size) {
        std::cerr << "Warning: " << umi_opcode_to_str(resp_opcode)
            << " response SIZE is " << std::to_string(resp_size)
            << " (expected " << std::to_string(expected_size) << ")" << std::endl;
    }

    if (resp_len != expected_len) {
        std::cerr << "Warning: " << umi_opcode_to_str(resp_opcode)
            << " response LEN is " << std::to_string(resp_len)
            << " (expected " << std::to_string(expected_len) << ")" << std::endl;
    }

    if (resp.dstaddr != expected_dstaddr) {
        std::cerr <<  "Warning: dstaddr in " << umi_opcode_to_str(resp_opcode)
            << " response is " << std::to_string(resp.dstaddr)
            << " (expected " << std::to_string(expected_dstaddr) << ")" << std::endl;
    }
}

// basic class for representing a UMI transaction, which may span
// multiple packets.

struct UmiTransaction {
    UmiTransaction(uint32_t cmd=0, uint64_t dstaddr=0, uint64_t srcaddr=0,
        uint8_t* data=NULL, size_t nbytes=0) : cmd(cmd), dstaddr(dstaddr),
        srcaddr(srcaddr), data(data), m_nbytes(nbytes), m_allocated(false) {

        if ((data == NULL) && (nbytes > 0)) {
            resize(nbytes);
        }

    }

    ~UmiTransaction() {
        if (m_allocated) {
            free(data);
        }
    }

    std::string toString() {
        return umi_transaction_as_str<UmiTransaction>(*this);
    }

    void resize(size_t n) {
        // allocate new space if needed
        if (n > m_nbytes) {
            if (m_allocated) {
                data = (uint8_t*)realloc(data, n);
            } else {
                data = (uint8_t*)malloc(n);
                m_allocated = true;
            }
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

    uint32_t cmd;
    uint64_t dstaddr;
    uint64_t srcaddr;
    uint8_t* data;

    private:
        size_t m_nbytes;
        bool m_allocated;
};

// higher-level functions for UMI transactions

template <typename T> static inline bool umisb_send(
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

    // load fields into an SB packet

    sb_packet p;
    umi_packet* up = (umi_packet*)p.data;

    up->cmd = x.cmd;
    up->dstaddr = x.dstaddr;
    up->srcaddr = x.srcaddr;

    uint32_t opcode = umi_opcode(x.cmd);

    if (opcode != UMI_REQ_READ) {
        uint32_t len = umi_len(x.cmd);
        uint32_t size = umi_size(x.cmd);
        uint32_t nbytes = (len+1)<<size;
        if (nbytes > sizeof(up->data)) {
            throw std::runtime_error(
                "(len+1)<<size cannot exceed the data payload size of a UMI packet.");
        }
        if (nbytes > x.nbytes()) {
            throw std::runtime_error(
                "(len+1)<<size cannot exceed the number of data bytes in the UMI transaction.");
        }
        memcpy(up->data, x.ptr(), nbytes);
    }

    bool header_sent = tx.send(p);
    if ((!blocking) && (!header_sent)) {
        return false;
    }

    // if we reach this point, we're committed to send out the whole UMI
    // transaction, which may span multiple packets

    // finish sending the header packet
    if (!header_sent) {
        while (!tx.send(p)) {
            if (loop) {
                loop();
            }
        }
    }

    // print out the packet sent if desired
    if (printer != NULL) {
        printer(p, true);
    }

    // if we reach this point, we succeeded in sending the packet
    return true;
}

template <typename T> static inline bool umisb_recv(
    T& x, SBRX& rx, bool blocking=true, void (*loop)(void)=NULL, PacketPrinter printer=NULL) {

    // if the receive side isn't active, there is nothing to receive
    if (!rx.is_active()) {
        return false;
    }

    // get a response

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

    umi_packet* up = (umi_packet*)p.data;

    if (printer != NULL) {
        printer(p, true);
    }

    // read information from the packet

    x.cmd = up->cmd;
    x.dstaddr = up->dstaddr;
    x.srcaddr = up->srcaddr;

    uint32_t opcode = umi_opcode(up->cmd);

    if (opcode != UMI_REQ_READ) {
        uint32_t len = umi_len(x.cmd);
        uint32_t size = umi_size(x.cmd);
        uint32_t nbytes = (len+1)<<size;
        x.resize(nbytes);
        if (nbytes > sizeof(up->data)) {
            throw std::runtime_error(
                "(len+1)<<size cannot exceed the data payload size of a UMI packet.");
        }
        memcpy(x.ptr(), up->data, nbytes);
    }

    return true;
}

#endif // __UMISB_HPP__
