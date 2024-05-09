// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __UMISB_HPP__
#define __UMISB_HPP__

#include <functional>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>

#include "switchboard.hpp"
#include "umilib.h"
#include "umilib.hpp"

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
        uint32_t len = umi_len(x.cmd) + 1;

        for (size_t i = 0; i < len; i++) {
            if ((i + 1) * (1 << size) <= nbytes) {
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
            if (i != (len - 1)) {
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

    stream << std::endl << "size: " << umi_size(x.cmd);
    stream << std::endl << "len: " << umi_len(x.cmd);
    stream << std::endl << "eom: " << umi_eom(x.cmd);
    stream << std::endl << "eof: " << umi_eof(x.cmd);

    // print out the data as long as this isn't a read request, since
    // that doesn't have data
    if (!((opcode == UMI_REQ_READ) || (opcode == UMI_REQ_RDMA))) {
        stream << std::endl << "data: " << umi_data_as_str<T>(x);
    }

    // return the result, noting that it does not contain a final newline
    return stream.str();
}

// function to print a warning or throw an error

static inline void umisb_error_or_warn(std::string const& msg, bool error = true) {
    if (error) {
        throw std::runtime_error(msg);
    } else {
        std::cerr << "Warning: " << msg << std::endl;
    }
}

// function for checking if requests and replies match up as expected

template <typename T>
void umisb_check_resp(T& resp, uint32_t opcode, uint32_t size, uint32_t to_ack,
    uint64_t expected_addr, bool error = true) {

    uint32_t resp_opcode = umi_opcode(resp.cmd);
    uint32_t resp_size = umi_size(resp.cmd);
    uint32_t resp_len = umi_len(resp.cmd);

    // check that the response makes sense

    if (resp_opcode != opcode) {
        std::ostringstream oss;
        oss << "Got " << umi_opcode_to_str(resp_opcode) << " (expected "
            << umi_opcode_to_str(opcode) << ")";
        umisb_error_or_warn(oss.str(), error);
    }

    if (resp_size != size) {
        std::ostringstream oss;
        oss << umi_opcode_to_str(resp_opcode) << " response SIZE is " << std::to_string(resp_size)
            << " (expected " << std::to_string(size) << ")";
        umisb_error_or_warn(oss.str(), error);
    }

    if ((resp_len + 1) > to_ack) {
        std::ostringstream oss;
        oss << umi_opcode_to_str(resp_opcode) << " response LEN is " << std::to_string(resp_len)
            << " (expected no more than " << std::to_string(to_ack - 1) << ")";
        umisb_error_or_warn(oss.str(), error);
    }

    if (resp.dstaddr != expected_addr) {
        std::ostringstream oss;
        oss << "dstaddr in " << umi_opcode_to_str(resp_opcode) << " response is "
            << std::to_string(resp.dstaddr) << " (expected " << std::to_string(expected_addr)
            << ")";
        umisb_error_or_warn(oss.str(), error);
    }
}

// basic class for representing a UMI transaction, which may span
// multiple packets.

struct UmiTransaction {
    UmiTransaction(uint32_t cmd = 0, uint64_t dstaddr = 0, uint64_t srcaddr = 0,
        uint8_t* data = NULL, size_t nbytes = 0)
        : cmd(cmd), dstaddr(dstaddr), srcaddr(srcaddr) {

        m_storage = false;
        m_allocated = false;
        m_nbytes = 0;

        if (data != NULL) {
            this->data = data;
            m_storage = true;
            m_nbytes = nbytes;
        } else if (nbytes > 0) {
            allocate(0, nbytes - 1);
        } else {
            this->data = NULL;
        }
    }

    ~UmiTransaction() {
        if (m_allocated) {
            delete[] data;
        }
    }

    std::string toString() {
        return umi_transaction_as_str<UmiTransaction>(*this);
    }

    void allocate(size_t size, size_t len) {
        // check that we can perform this operation

        if (m_storage) {
            throw std::runtime_error(
                "There is already storage for this UMI transaction, no need to allocate.");
        }

        if (m_allocated) {
            throw std::runtime_error("Memory has already been allocated for this UMI transaction.");
        }

        // allocate the memory

        size_t nbytes = (len + 1) << size;
        data = new uint8_t[nbytes];

        // indicate that storage is now available for this transaction,
        // and that we allocated memory to make it available

        m_storage = true;
        m_allocated = true;
        m_nbytes = nbytes;
    }

    bool storage() {
        return m_storage;
    }

    size_t nbytes() {
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
    bool m_storage;
};

// higher-level functions for UMI transactions

template <typename T>
static inline bool umisb_send(T& x, SBTX& tx, bool blocking = true, void (*loop)(void) = NULL) {

    // sends (or tries to send, if blocking=false) a single UMI transaction

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

    if ((opcode == UMI_REQ_READ) || (opcode == UMI_REQ_RDMA) || (opcode == UMI_RESP_WRITE)) {
        // do nothing, since there isn't data to copy
    } else {
        uint32_t size = umi_size(x.cmd);
        uint32_t len = umi_len(x.cmd);

        size_t nbytes = (len + 1) << size;

        if (nbytes > sizeof(up->data)) {
            throw std::runtime_error(
                "umisb_send: (len+1)<<size cannot exceed the data size of a umi_packet.");
        }

        if (nbytes > x.nbytes()) {
            throw std::runtime_error(
                "umisb_send: (len+1)<<size cannot exceed the data size of a UmiTransaction.");
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
        bool success = false;

        while (!success) {
            success = tx.send(p);

            if (loop) {
                loop();
            }
        }
    }

    // if we reach this point, we succeeded in sending the packet
    return true;
}

template <typename T>
static inline bool umisb_recv(T& x, SBRX& rx, bool blocking = true, void (*loop)(void) = NULL) {

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
        bool success = false;

        while (!success) {
            success = rx.recv(p);

            if (loop) {
                loop();
            }
        }
    }

    // if we get to this point, there is valid data in "p"

    umi_packet* up = (umi_packet*)p.data;

    // read information from the packet

    x.cmd = up->cmd;
    x.dstaddr = up->dstaddr;
    x.srcaddr = up->srcaddr;

    uint32_t opcode = umi_opcode(up->cmd);

    if ((opcode == UMI_REQ_READ) || (opcode == UMI_REQ_RDMA) || (opcode == UMI_RESP_WRITE)) {
        // do nothing, since there isn't data to copy
    } else {
        uint32_t size = umi_size(x.cmd);
        uint32_t len = umi_len(x.cmd);

        if (!x.storage()) {
            x.allocate(size, len);
        }

        size_t nbytes = (len + 1) << size;

        if (nbytes > sizeof(up->data)) {
            throw std::runtime_error(
                "umisb_recv: (len+1)<<size cannot exceed the data size of a umi_packet.");
        }

        if (nbytes > x.nbytes()) {
            throw std::runtime_error(
                "umisb_recv: (len+1)<<size cannot exceed the data size of a UmiTransaction.");
        }

        memcpy(x.ptr(), up->data, nbytes);
    }

    return true;
}

#endif // __UMISB_HPP__
