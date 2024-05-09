// Python binding for Switchboard

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <cstring>
#include <exception>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <stdio.h>

#include <pybind11/numpy.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "bitutil.h"
#include "bytesobject.h"
#include "object.h"
#include "pybind11/buffer_info.h"
#include "pybind11/detail/common.h"
#include "pybind11/pytypes.h"
#include "switchboard.hpp"
#include "switchboard_pcie.hpp"
#include "umilib.h"
#include "umilib.hpp"
#include "umisb.hpp"

namespace py = pybind11;

// PySbPacket: pybind-friendly representation of sb_packet
// This is needed because pybind11 does not have a method
// for directly interfacing with C-style arrays, which are
// used in sb_packet.  A basic question to explore in the
// future is whether is is possible to use sb_packet more
// directly via pybinds's buffer protocol.

struct PySbPacket {
    // in the constructor, we cannot simply set the default value for
    // data to a py::array_t, since that array would only be created
    // once, and shared among instances of this class that used the
    // default value, which is not required.  hence, as would be done
    // in python, the default value of "data" is set to None, and
    // then a new py::array_t instance is created in the body of the
    // initialization

    PySbPacket(uint32_t destination = 0, uint32_t flags = 0,
        std::optional<py::array_t<uint8_t>> data = std::nullopt)
        : destination(destination), flags(flags) {
        if (data.has_value()) {
            this->data = data.value();
        } else {
            this->data = py::array_t<uint8_t>(SB_DATA_SIZE);
        }
    }

    std::string toString() {
        std::stringstream stream;
        stream << "dest: " << destination << std::endl;
        stream << "last: " << (flags & 1) << std::endl;
        stream << "data: " << py::str(data);
        return stream.str();
    }

    uint32_t destination;
    uint32_t flags;
    py::array_t<uint8_t> data;
};

// functions for allocating and accessing the pointer to pybind arrays

py::array alloc_pybind_array(int num, size_t bytes_per_elem = 1) {
    if (bytes_per_elem == 1) {
        return py::array_t<uint8_t>(num);
    } else if (bytes_per_elem == 2) {
        return py::array_t<uint16_t>(num);
    } else if (bytes_per_elem == 4) {
        return py::array_t<uint32_t>(num);
    } else if (bytes_per_elem == 8) {
        return py::array_t<uint64_t>(num);
    } else {
        throw std::runtime_error("Unsupported value for bytes_per_elem.");
    }
}

uint8_t* get_pybind_array_ptr(py::array arr) {
    py::buffer_info info = py::buffer(arr).request();
    return (uint8_t*)info.ptr;
}

// As with PySbPacket, PyUmiPacket makes the contents of umi_packet
// accessible in a pybind-friendly manner.  The same comments about
// setting the default value of the data argument to "None" apply.

struct PyUmiPacket {
    PyUmiPacket(uint32_t cmd = 0, uint64_t dstaddr = 0, uint64_t srcaddr = 0,
        std::optional<py::array> data = std::nullopt, size_t nbytes = 0)
        : cmd(cmd), dstaddr(dstaddr), srcaddr(srcaddr) {

        m_allocated = false;
        m_storage = false;

        if (data.has_value()) {
            this->data = data.value();
            m_storage = true;
        } else if (nbytes > 0) {
            allocate(0, nbytes - 1);
        }
    }

    std::string toString() {
        return umi_transaction_as_str<PyUmiPacket>(*this);
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

        data = alloc_pybind_array((len + 1), (1 << size));

        // indicate that storage is now available for this transaction,
        // and that we allocated memory to make it available

        m_storage = true;
        m_allocated = true;
    }

    void resize(size_t size, size_t len) {
        if (!m_storage) {
            throw std::runtime_error("There is not storage associated with this UMI transaction.");
        } else {
            if (data.itemsize() != (1 << size)) {
                throw std::runtime_error("Array data type doesn't match SIZE.");
            }

            data.resize({len + 1});
        }
    }

    bool storage() {
        return m_storage;
    }

    size_t nbytes() {
        py::buffer_info info = py::buffer(data).request();
        return info.itemsize * info.size;
    }

    uint8_t* ptr() {
        py::buffer_info info = py::buffer(data).request();
        return (uint8_t*)info.ptr;
    }

    uint32_t cmd;
    uint64_t dstaddr;
    uint64_t srcaddr;
    py::array data;

    bool merge(const PyUmiPacket& other) {
        uint32_t opcode = umi_opcode(cmd);

        if (!allows_umi_merge(opcode)) {
            // merging is not allowed for this kind of transaction
            return false;
        }

        if (umi_ex(cmd) != 0) {
            // merging is only allowed when ex == 0
            return false;
        }

        // check that all fields except EOM and LEN match
        uint32_t mask = 0xffffffff;
        set_umi_eom(&mask, 0);
        set_umi_len(&mask, 0);
        if ((cmd & mask) != (other.cmd & mask)) {
            return false;
        }

        if (umi_eom(cmd)) {
            // when merging a sequence of packets, only the last
            // packet can have eom=1
            return false;
        }

        uint32_t size = umi_size(cmd);
        uint32_t len = umi_len(cmd);
        uint32_t nbytes = (len + 1) << size;

        if (other.dstaddr != (dstaddr + nbytes)) {
            // new dstaddr must be next sequentially
            return false;
        }

        if (other.srcaddr != (srcaddr + nbytes)) {
            // new srcaddr must be next sequentially
            return false;
        }

        if (has_umi_data(opcode)) {
            // resize this packet
            resize(size, len + umi_len(other.cmd) + 1);

            // make sure the data indicated by the command is there
            uint32_t other_len = umi_len(other.cmd);
            uint32_t other_nbytes = (other_len + 1) << size;
            if (other.data.nbytes() < other_nbytes) {
                throw std::runtime_error("other packet doesn't contain enough data");
            }

            // copy in the data
            uint8_t* ptr = (uint8_t*)py::buffer(data).request().ptr;
            uint8_t* other_ptr = (uint8_t*)py::buffer(other.data).request().ptr;
            memcpy(ptr + nbytes, other_ptr, other_nbytes);
        }

        // set LEN
        set_umi_len(&cmd, len + umi_len(other.cmd) + 1);

        // set EOM
        set_umi_eom(&cmd, umi_eom(other.cmd));

        return true;
    }

    bool friend operator==(const PyUmiPacket& lhs, const PyUmiPacket& rhs) {
        if (((lhs.cmd & 0xff) == 0) && ((rhs.cmd & 0xff) == 0)) {
            // both are invalid; only the first 8 bits of the command
            // have to match in order for the packets to be considered
            // equivalent
            return true;
        }

        if (lhs.cmd != rhs.cmd) {
            // commands match
            return false;
        }

        // if we get to this point, the commands match, so we can
        // just work with the command from the left-hand side

        uint32_t cmd = lhs.cmd;
        uint32_t opcode = umi_opcode(cmd);

        if ((opcode == UMI_REQ_LINK) || (opcode == UMI_RESP_LINK)) {
            // link commands have no address or data, so the comparison
            // is done at this point
            return true;
        }

        // all other commands have a destination address, which must match
        // between lhs and rhs

        if (lhs.dstaddr != rhs.dstaddr) {
            return false;
        }

        if (is_umi_req(opcode) && (lhs.srcaddr != rhs.srcaddr)) {
            // requests also have a source address, which must match
            // between lhs and rhs
            return false;
        }

        if (has_umi_data(opcode)) {
            uint32_t len = umi_len(cmd);
            uint32_t size = umi_size(cmd);
            uint32_t nbytes = (len + 1) << size;

            if ((lhs.data.nbytes() < nbytes) || (rhs.data.nbytes() < nbytes)) {
                // one packet or both doesn't have enough data to compare
                return false;
            }

            py::buffer_info lhs_info = py::buffer(lhs.data).request();
            py::buffer_info rhs_info = py::buffer(rhs.data).request();

            if (memcmp(lhs_info.ptr, rhs_info.ptr, nbytes) != 0) {
                // note that memcpy returns "0" if the arrays match,
                // so we'll only get here if there is a mismatch
                return false;
            }
        }

        return true;
    }

    bool friend operator!=(const PyUmiPacket& lhs, const PyUmiPacket& rhs) {
        return !(lhs == rhs);
    }

  private:
    bool m_allocated;
    bool m_storage;
};

// check_signals() should be called within any loops where the C++
// code is waiting for something to happen.  this ensures that
// the binding doesn't hang after the user presses Ctrl-C.

void check_signals() {
    if (PyErr_CheckSignals() != 0) {
        throw pybind11::error_already_set();
    }
}

// PySbTxPcie / PySbRxPcie: these objects must be created to initialize Switchboard
// queues that are accessed over PCIe.  Care must be taken to ensure that they
// don't go out of scope, since that will invoke destructors that deinitialize
// the queues.

struct PySbTxPcie {
    PySbTxPcie(std::string uri = "", int idx = 0, int bar_num = 0, std::string bdf = "") {
        init(uri, idx, bar_num, bdf);
    }

    void init(std::string uri = "", int idx = 0, int bar_num = 0, std::string bdf = "") {
        if ((uri != "") && (bdf != "")) {
            m_tx = std::unique_ptr<SBTX_pcie>(new SBTX_pcie(idx));
            if (!m_tx->init(uri, bdf, bar_num)) {
                throw std::runtime_error("Unable to initialize PCIe TX Queue.");
            }
        }
    }

  private:
    std::unique_ptr<SBTX_pcie> m_tx;
};

struct PySbRxPcie {
    PySbRxPcie(std::string uri = "", int idx = 0, int bar_num = 0, std::string bdf = "") {
        init(uri, idx, bar_num, bdf);
    }

    void init(std::string uri = "", int idx = 0, int bar_num = 0, std::string bdf = "") {
        if ((uri != "") && (bdf != "")) {
            m_rx = std::unique_ptr<SBRX_pcie>(new SBRX_pcie(idx));
            if (!m_rx->init(uri, bdf, bar_num)) {
                throw std::runtime_error("Unable to initialize PCIe RX Queue.");
            }
        }
    }

  private:
    std::unique_ptr<SBRX_pcie> m_rx;
};

// fpga_init_tx: initialize an FPGA TX queue

// PySbTx: pybind-friendly version of SBTX that works with PySbPacket

class PySbTx {
  public:
    PySbTx(std::string uri = "", bool fresh = false, double max_rate = -1) {
        init(uri, fresh, max_rate);
    }

    void init(std::string uri, bool fresh = false, double max_rate = -1) {
        if (uri != "") {
            m_tx.init(uri, 0, fresh, max_rate);
        }
    }

    bool send(const PySbPacket& py_packet, bool blocking = true) {
        // if blocking=true (default), this function will keep trying
        // to send a packet until it is successful, at which point the
        // function returns "true".  otherwise, the send will only be
        // attempted once, and the boolean value returned indicates
        // whether that send was successful.

        // make sure "data" is formatted correctly.  workaround for accessing bytes
        // is discussed here: https://github.com/pybind/pybind11/issues/2517#issuecomment-696900575

        py::buffer_info info = py::buffer(py_packet.data).request();

        pybind11::ssize_t len = info.size;
        if (len > SB_DATA_SIZE) {
            len = SB_DATA_SIZE;
        }

        // convert data to be sent to an sb_packet
        // TODO: try to avoid copying data

        sb_packet p;
        p.destination = py_packet.destination;
        p.flags = py_packet.flags;
        if (len > 0) {
            memcpy(p.data, info.ptr, len);
        }

        // try to send the packet once or multiple times depending
        // on the "blocking" argument

        if (!blocking) {
            return m_tx.send(p);
        } else {
            while (!m_tx.send(p)) {
                check_signals();
            }

            return true;
        }
    }

  private:
    SBTX m_tx;
};

// PySbTx: pybind-friendly version of SBTX that works with PySbPacket

class PySbRx {
  public:
    PySbRx(std::string uri = "", bool fresh = false, double max_rate = -1) {
        init(uri, fresh, max_rate);
    }

    void init(std::string uri, bool fresh = false, double max_rate = -1) {
        if (uri != "") {
            m_rx.init(uri, 0, fresh, max_rate);
        }
    }

    std::unique_ptr<PySbPacket> recv(bool blocking = true) {
        // if blocking=true (default), this function will keep trying to
        // receive a packet until it gets one, returning the result as
        // a PySbPacket.  otherwise, it will try just once, returning
        // a PySbPacket if successful, and None otherwise

        sb_packet p;
        if (!blocking) {
            if (!m_rx.recv(p)) {
                return nullptr;
            }
        } else {
            while (!m_rx.recv(p)) {
                check_signals();
            }
        }

        // if we get to this point, there is valid data in "p"

        // create "py_packet" to hold received data in a pybind-friendly manner
        std::unique_ptr<PySbPacket> py_packet(new PySbPacket(p.destination, p.flags));

        // copy data from "p" to "py_packet"
        // TODO: can this be avoided?
        py::buffer_info info = py::buffer(py_packet->data).request();
        memcpy(info.ptr, p.data, SB_DATA_SIZE);

        // return the packet
        return py_packet;
    }

  private:
    SBRX m_rx;
};

// Functions to show a progress bar.

static void progressbar_show(int& state, uint64_t progress, uint64_t total) {
    unsigned int progress_percent = progress * 100 / total;
    // Cap it to 50 chars for smaller terminals.
    unsigned int count = progress_percent / 2;

    if (count == state)
        return;
    state = count;

    putchar('\r');
    printf("%d%%\t", progress_percent);
    while (count--) {
        putchar('#');
    }
    fflush(stdout);
}

static inline void progressbar_done(void) {
    putchar('\n');
}

// PyUmi: Higher-level than PySbTx and PySbRx, this class works with two SB queues,
// one TX and one RX, to issue write requests and read requests according to the UMI
// specification.

class PyUmi {
  public:
    PyUmi(std::string tx_uri = "", std::string rx_uri = "", bool fresh = false,
        double max_rate = -1) {
        init(tx_uri, rx_uri, fresh, max_rate);
    }

    void init(std::string tx_uri, std::string rx_uri, bool fresh = false, double max_rate = -1) {
        if (tx_uri != "") {
            m_tx.init(tx_uri, 0, fresh, max_rate);
        }
        if (rx_uri != "") {
            m_rx.init(rx_uri, 0, fresh, max_rate);
        }
    }

    bool send(PyUmiPacket& py_packet, bool blocking = true) {
        // sends (or tries to send, if blocking=false) a single UMI transaction
        // if length of the data payload in the packet is greater than
        // what can be sent in a header packet, then a header packet is sent
        // containing the beginning of the data, followed by the rest in
        // subsequent burst packets.

        return umisb_send<PyUmiPacket>(py_packet, m_tx, blocking, &check_signals);
    }

    std::unique_ptr<PyUmiPacket> recv(bool blocking = true) {
        // try to receive a transaction
        std::unique_ptr<PyUmiPacket> resp = std::unique_ptr<PyUmiPacket>(new PyUmiPacket());
        bool success = umisb_recv<PyUmiPacket>(*resp.get(), m_rx, blocking, &check_signals);

        // if we got something, return it, otherwise return a null pointer
        if (success) {
            return resp;
        } else {
            return nullptr;
        }
    }

    void write(uint64_t addr, py::array data, uint64_t srcaddr = 0,
        uint32_t max_bytes = UMI_PACKET_DATA_BYTES, bool posted = false, uint32_t qos = 0,
        uint32_t prot = 0, bool progressbar = false, bool error = true) {

        // write data to the given address.  data can be of any length,
        // including greater than the length of a header packet and
        // values that are not powers of two.  this function is blocking.

        // get access to the data
        py::buffer_info info = py::buffer(data).request();

        // make sure that max_bytes is set appropriately.

        // I thought about directly reading the size of the data payload
        // from the umi_packet struct, but the mechanism for doing this
        // is fairly hard to read: sizeof(((umi_packet*)NULL)->data).  It
        // seemed clearer to define a new constant that refers to the size
        // the UMI packet data payload.  Eventually, we will make this
        // payload size configurable so that different SUMI bus widths
        // can be represented.  SGH 7/24/23

        if (max_bytes > UMI_PACKET_DATA_BYTES) {
            printf("WARNING: max_bytes is greater than the data payload"
                   " of a single UMI packet (%d vs. %d bytes).  Change max_bytes"
                   " to %d or smaller to clear this warning.\n",
                max_bytes, UMI_PACKET_DATA_BYTES, UMI_PACKET_DATA_BYTES);
            max_bytes = UMI_PACKET_DATA_BYTES;
        }

        if (max_bytes < info.itemsize) {
            throw std::runtime_error(
                "max_bytes must be greater than or equal to the word size in bytes.");
        }

        // if there is nothing to write, return
        uint32_t total_len = info.size;
        if (total_len <= 0) {
            return;
        }

        // fields only used if expecting a write response
        uint32_t to_ack = total_len;
        uint64_t expected_addr = srcaddr;

        // otherwise get the data pointer and decompose the data into
        // power-of-two chunks, with the size of each chunk being the
        // largest that is possible while remaining aligned, and
        // without exceeding the number of remaining bytes.

        uint8_t* ptr = (uint8_t*)info.ptr;

        // determine the opcode to use
        uint32_t opcode = posted ? UMI_REQ_POSTED : UMI_REQ_WRITE;

        // determine the size of individual items
        uint32_t size = highest_bit(info.itemsize);

        // determine the maximum length of an individual packet
        uint32_t max_len = max_bytes / info.itemsize;
        int pb_state = 0;

        // send all of the data
        while ((total_len > 0) || ((!posted) && (to_ack > 0))) {
            if (total_len > 0) {
                // try to send a write request
                uint32_t len = std::min(total_len, max_len);
                uint32_t eom = (len == total_len) ? 1 : 0;
                uint32_t cmd = umi_pack(opcode, 0, size, len - 1, eom, 1, qos, prot);
                UmiTransaction req(cmd, addr, srcaddr, ptr, len << size);
                if (umisb_send<UmiTransaction>(req, m_tx, false)) {
                    // update pointers
                    total_len -= len;
                    ptr += len << size;
                    addr += len << size;
                    srcaddr += len << size;

                    if (posted && progressbar) {
                        progressbar_show(pb_state, info.size - total_len, info.size);
                    }
                }
            }

            if ((!posted) && (to_ack > 0)) {
                UmiTransaction resp(0, 0, 0, NULL, 0);
                if (umisb_recv<UmiTransaction>(resp, m_rx, false)) {
                    // check that the response makes sense
                    umisb_check_resp(resp, UMI_RESP_WRITE, size, to_ack, expected_addr, error);

                    // update ack status
                    to_ack -= (umi_len(resp.cmd) + 1);
                    expected_addr += (umi_len(resp.cmd) + 1) << umi_size(resp.cmd);

                    if (!posted && progressbar) {
                        progressbar_show(pb_state, info.size - to_ack, info.size);
                    }
                }
            }

            // make sure there aren't outside signals trying to interrupt
            check_signals();
        }
        if (progressbar) {
            progressbar_done();
        }
    }

    py::array read(uint64_t addr, uint32_t num, size_t bytes_per_elem, uint64_t srcaddr = 0,
        uint32_t max_bytes = UMI_PACKET_DATA_BYTES, uint32_t qos = 0, uint32_t prot = 0,
        bool error = true) {

        // read "num" bytes from the given address.  "num" may be any value,
        // including greater than the length of a header packet, and values
        // that are not powers of two.  the optional "srcaddr" argument is
        // the source address to which responses should be sent.  this
        // function is blocking.

        // make sure that max_bytes is set appropriately

        if (max_bytes > UMI_PACKET_DATA_BYTES) {
            printf("WARNING: max_bytes is greater than the data payload"
                   " of a single UMI packet (%d vs. %d bytes).  Change max_bytes"
                   " to %d or smaller to clear this warning.\n",
                max_bytes, UMI_PACKET_DATA_BYTES, UMI_PACKET_DATA_BYTES);
            max_bytes = UMI_PACKET_DATA_BYTES;
        }

        if (max_bytes < bytes_per_elem) {
            throw std::runtime_error("max_bytes must be greater than or equal to bytes_per_elem.");
        }

        // create a buffer to hold the result
        py::array result = alloc_pybind_array(num, bytes_per_elem);

        if (num == 0) {
            // nothing to read, so just return the empty array
            return result;
        }

        // otherwise get the data pointer and read the data in
        // power-of-two chunks, with the size of each chunk being the
        // largest that is possible while remaining aligned, and
        // without exceeding the number of remaining bytes.

        py::buffer_info info = py::buffer(result).request();
        uint8_t* ptr = (uint8_t*)info.ptr;

        // determine the size of individual items
        uint32_t size = highest_bit(bytes_per_elem);

        // determine the maximum length of an individual packet
        uint32_t max_len = max_bytes / bytes_per_elem;

        // used to keep track of responses
        uint32_t to_recv = num;
        uint64_t expected_addr = srcaddr;

        while ((num > 0) || (to_recv > 0)) {
            if (num > 0) {
                // send read request
                uint32_t len = std::min(num, max_len);
                uint32_t eom = (len == num) ? 1 : 0;
                uint32_t cmd = umi_pack(UMI_REQ_READ, 0, size, len - 1, eom, 1, qos, prot);
                UmiTransaction request(cmd, addr, srcaddr);
                if (umisb_send<UmiTransaction>(request, m_tx, false)) {
                    // update pointers
                    num -= len;
                    addr += len << size;
                    srcaddr += len << size;
                }
            }

            if (to_recv > 0) {
                // get read response
                uint32_t max_resp_bytes = to_recv << size;
                UmiTransaction resp(0, 0, 0, ptr, max_resp_bytes);
                if (umisb_recv<UmiTransaction>(resp, m_rx, false)) {
                    // check that the reply makes sense
                    umisb_check_resp<UmiTransaction>(resp, UMI_RESP_READ, size, to_recv,
                        expected_addr, error);

                    // update pointers
                    ptr += (umi_len(resp.cmd) + 1) << umi_size(resp.cmd);
                    expected_addr += (umi_len(resp.cmd) + 1) << umi_size(resp.cmd);
                    to_recv -= (umi_len(resp.cmd) + 1);
                }
            }

            // make sure there aren't outside signals trying to interrupt
            check_signals();
        }

        return result;
    }

    py::array atomic(uint64_t addr, py::array_t<uint8_t> data, uint32_t opcode,
        uint64_t srcaddr = 0, uint32_t qos = 0, uint32_t prot = 0, bool error = true) {
        // input validation

        uint32_t num = data.nbytes();

        if (num == 0) {
            // nothing to read, so just return the empty array
            return py::array_t<uint8_t>(0);
        }

        uint32_t size = highest_bit(num);

        if (size > 3) {
            throw std::runtime_error("Atomic operand must be 8 bytes or fewer.");
        }

        if (num != (1 << size)) {
            throw std::runtime_error(
                "Width of atomic operand must be a power of two number of bytes.");
        }

        // format the request
        uint32_t cmd = umi_pack(UMI_REQ_ATOMIC, opcode, size, 0, 1, 1, qos, prot);
        PyUmiPacket request(cmd, addr, srcaddr, data);

        // send the request
        umisb_send<PyUmiPacket>(request, m_tx, true, &check_signals);

        // get the response
        PyUmiPacket resp;
        umisb_recv<PyUmiPacket>(resp, m_rx, true, &check_signals);

        // check that the response makes sense
        umisb_check_resp(resp, UMI_RESP_READ, size, 1, srcaddr, error);

        // return the result of the operation
        return resp.data;
    }

  private:
    SBTX m_tx;
    SBRX m_rx;
};

// convenience function to delete old queues from previous runs

void delete_queue(std::string uri) {
    delete_shared_queue(uri);
}

void delete_queues(const std::vector<std::string>& uri_list) {
    for (const std::string& uri : uri_list) {
        delete_shared_queue(uri);
    }
}

// doc strings for important/commonly used pybind functions below
char* PySbTx_init_docstring = "Parameters\n"
                              "----------\n"
                              "uri: str\n"
                              "\tName of the queue for the Tx object\n"
                              "fresh: bool, optional\n"
                              "\tIf True, the queue specified by the `uri` parameter"
                              " will get cleared before executing the simulation.";

char* PySbTx_send_docstring = "Parameters\n"
                              "----------\n"
                              "py_packet: PySbPacket\n"
                              "\tUMI packet to send\n"
                              "blocking: bool, optional\n"
                              "\tIf true, the function will pause execution until the"
                              " packet has been successfully sent.";

char* PySbRx_init_docstring = "Parameters\n"
                              "----------\n"
                              "uri: str"
                              "\tName of the queue for the Rx object\n"
                              "fresh: bool, optional\n"
                              "\tIf True, the queue specified by the `uri` parameter"
                              " will get cleared before executing the simulation.";

char* PySbRx_recv_docstring =
    "Parameters\n"
    "----------\n"
    "blocking: bool, optional\n"
    "\tIf true, the function will pause execution until a packet"
    "can be read. If false, the function will return None if a packet"
    "cannot be read immediately\n"
    "Returns\n"
    "-------\n"
    "PySbPacket\n"
    "\tReturns a UMI packet. If `blocking` is false, None will be returned"
    " If a packet cannot be read immediately.";

char* PyUmi_init_docstring =
    "Parameters\n"
    "----------\n"
    "tx_uri: str, optional\n"
    "\tName of the switchboard queue that write() and send() will send UMI packets to."
    " Defaults to None, meaning “unused”.\n"
    "rx_uri: str, optional\n"
    "\tName of the switchboard queue that read() and recv() will receive UMI packets from."
    " Defaults to None, meaning “unused”.\n"
    "fresh: bool, optional\n"
    "\tIf true, the `tx_uri` and `rx_uri` will be cleared prior to running";

char* PyUmi_send_docstring = "Parameters\n"
                             "----------\n"
                             "py_packet: PySbPacket\n"
                             "\tUMI packet to send\n"
                             "blocking: bool, optional\n"
                             "\tIf true, the function will pause execution until the"
                             " packet has been successfully sent.";

char* PyUmi_recv_docstring = "Parameters\n"
                             "----------\n"
                             "blocking: bool, optional\n"
                             "\tIf true, the function will pause execution until a packet"
                             "can be read. If false, the function will return None if a packet"
                             "cannot be read immediately\n"
                             "Returns\n"
                             "-------\n"
                             "PySbPacket\n"
                             "\tReturns a UMI packet. If `blocking` is false, None will be returned"
                             " If a packet cannot be read immediately.";

char* PyUmi_write_docstring =
    "Parameters\n"
    "----------\n"
    "addr: int\n"
    "\t64-bit address that will be written to\n"
    "data: np.uint8, np.uint16, np.uint32, np.uint64, or np.array\n"
    "\tCan be either a numpy integer type (e.g., np.uint32) or an numpy"
    " array of integer types (np.uint8, np.uin16, np.uint32, np.uint64, etc.)."
    " The `data` input may contain more than `max_bytes`, in which case"
    " the write will automatically be split into multiple transactions.\n"
    "srcaddr: int, optional\n"
    "\tUMI source address used for the write transaction. This is sometimes needed to make"
    " the write response gets routed to the right place.\n"
    "max_bytes: int, optional\n"
    "\tIndicates the maximum number of bytesthat can be used for any"
    " individual UMI transaction in bytes. Currently, the data payload"
    " size used by switchboard is 32 bytes, which is reflected in the default"
    " value of `max_bytes`.\n"
    "posted: bool, optional\n"
    "\tIf True, a write response will be received.\n"
    "qos: int, optional\n"
    "\t4-bit Quality of Service field in UMI Command\n"
    "prot: int, optional\n"
    "\t2-bit protection mode field in UMI command\n"
    "progressbar: bool, optional\n"
    "\tIf True, the number of packets written will be displayed via a progressbar"
    "in the terminal.\n"
    "error: bool, optional\n"
    "\tIf true, error out upon receiving an unexpected UMI response.\n";

char* PyUmi_read_docstring =
    "Parameters\n"
    "----------\n"
    "addr: int\n"
    "\tThe 64-bit address read from\n"
    "num_or_dtype: int or numpy integer datatype\n"
    "\tIf a plain int, `num_or_datatype` specifies the number of bytes to be read."
    "If a numpy integer datatype (np.uint8, np.uint16, etc.), num_or_datatype"
    "specifies the data type to be returned.\n"
    "dtype: numpy integer datatype, optional\n"
    "\tIf num_or_dtype is a plain integer, the value returned by this function"
    "will be a numpy array of type `dtype`.  On the other hand, if num_or_dtype"
    "is a numpy datatype, the value returned will be a scalar of that datatype.\n"
    "srcaddr: int, optional\n"
    "\tThe UMI source address used for the read transaction. This"
    "is sometimes needed to make sure that reads get routed to the right place.\n"
    "max_bytes: int, optional\n"
    "\tIndicates the maximum number of bytes that can be used for any individual"
    "UMI transaction. `num_or_dtype` can be larger than `max_bytes`, in which"
    "case the read will automatically be split into multiple transactions. Currently,"
    "the data payload size used by switchboard is 32 bytes, which is reflected in the"
    "default value of `max_bytes`.\n"
    "qos: int, optional\n"
    "\t4-bit Quality of Service field in UMI Command\n"
    "prot: int, optional\n"
    "\t2-bit protection mode field in UMI command\n"
    "error: bool, optional\n"
    "\tIf true, error out upon receiving an unexpected UMI response.\n";

char* PyUmi_atomic_docstring =
    "Parameters\n"
    "----------\n"
    "addr: int\n"
    "\t64-bit address atomic operation will be applied to.\n"
    "data: np.uint8, np.uint16, np.uint32, np.uint64\n"
    "\tmust so that the size of the atomic operation can be determined.\n"
    "opcode: str or switchboard.UmiAtomic value\n"
    "\tSupported string values are 'add', 'and', 'or', 'xor', 'max', 'min',"
    " 'minu', 'maxu', and 'swap' (case-insensitive).\n"
    "srcaddr: int, optional\n"
    "\tThe UMI source address used for the atomic transaction. This"
    " is sometimes needed to make sure the response get routed to the right place.\n"
    "qos: int, optional\n"
    "\t4-bit Quality of Service field in UMI Command\n"
    "prot: int, optional\n"
    "\t2-bit protection mode field in UMI command\n"
    "error: bool, optional\n"
    "\tIf true, error out upon receiving an unexpected UMI response.\n"
    "Returns\n"
    "-------\n"
    "np.uint8, np.uint16, np.uint32, np.uint64\n"
    "\tThe value returned by this function is the original value at addr,"
    " immediately before the atomic operation is applied.  The numpy dtype of the"
    " returned value will be the same as for `data`.";

// Python bindings follow below.  There is some duplication of information in the default
// values for functions, but this is unavoidable for pybind.  Note also that the "toString"
// method of various classes is bound to "__str__", which has a special meaning in Python.
// This allows print() to be directly called on the object, which is convenient for debugging.
// It was assumed that directly using the name "__str__" instead of "toString" could be
// problematic because some C++ compilers assign special meanings to names starting with a
// double underscore, but it would be interesting to explore this in the future.

PYBIND11_MODULE(_switchboard, m) {
    m.doc() = "switchboard pybind11 plugin";

    py::class_<PySbPacket>(m, "PySbPacket")
        .def(py::init<uint32_t, uint32_t, std::optional<py::array_t<uint8_t>>>(),
            py::arg("destination") = 0, py::arg("flags") = 0, py::arg("data") = py::none())
        .def("__str__", &PySbPacket::toString)
        .def_readwrite("destination", &PySbPacket::destination)
        .def_readwrite("flags", &PySbPacket::flags)
        .def_readwrite("data", &PySbPacket::data);

    py::class_<PyUmiPacket>(m, "PyUmiPacket")
        .def(py::init<uint32_t, uint64_t, uint64_t, std::optional<py::array>>(), py::arg("cmd") = 0,
            py::arg("dstaddr") = 0, py::arg("srcaddr") = 0, py::arg("data") = py::none())
        .def("__str__", &PyUmiPacket::toString)
        .def("merge", &PyUmiPacket::merge)
        .def_readwrite("cmd", &PyUmiPacket::cmd)
        .def_readwrite("dstaddr", &PyUmiPacket::dstaddr)
        .def_readwrite("srcaddr", &PyUmiPacket::srcaddr)
        .def_readwrite("data", &PyUmiPacket::data)
        .def(py::self == py::self)
        .def(py::self != py::self);

    py::class_<PySbTx>(m, "PySbTx")
        .def(py::init<std::string, bool, double>(), py::arg("uri") = "", py::arg("fresh") = false,
            py::arg("max_rate") = -1)
        .def("init", &PySbTx::init, PySbTx_init_docstring, py::arg("uri") = "",
            py::arg("fresh") = false, py::arg("max_rate") = -1)
        .def("send", &PySbTx::send, PySbTx_send_docstring, py::arg("py_packet"),
            py::arg("blocking") = true);

    py::class_<PySbRx>(m, "PySbRx")
        .def(py::init<std::string, bool, double>(), py::arg("uri") = "", py::arg("fresh") = false,
            py::arg("max_rate") = -1)
        .def("init", &PySbRx::init, PySbRx_init_docstring, py::arg("uri") = "",
            py::arg("fresh") = false, py::arg("max_rate") = -1)
        .def("recv", &PySbRx::recv, PySbRx_recv_docstring, py::arg("blocking") = true);

    py::class_<PySbTxPcie>(m, "PySbTxPcie")
        .def(py::init<std::string, int, int, std::string>(), py::arg("uri") = "",
            py::arg("idx") = 0, py::arg("bar_num") = 0, py::arg("bdf") = "")
        .def("init", &PySbTxPcie::init, py::arg("uri") = "", py::arg("idx") = 0,
            py::arg("bar_num") = 0, py::arg("bdf") = "");

    py::class_<PySbRxPcie>(m, "PySbRxPcie")
        .def(py::init<std::string, int, int, std::string>(), py::arg("uri") = "",
            py::arg("idx") = 0, py::arg("bar_num") = 0, py::arg("bdf") = "")
        .def("init", &PySbRxPcie::init, py::arg("uri") = "", py::arg("idx") = 0,
            py::arg("bar_num") = 0, py::arg("bdf") = "");

    py::class_<PyUmi>(m, "PyUmi")
        .def(py::init<std::string, std::string, bool, double>(), py::arg("tx_uri") = "",
            py::arg("rx_uri") = "", py::arg("fresh") = false, py::arg("max_rate") = -1)
        .def("init", &PyUmi::init, PyUmi_init_docstring, py::arg("tx_uri") = "",
            py::arg("rx_uri") = "", py::arg("fresh") = false, py::arg("max_rate") = -1)
        .def("send", &PyUmi::send, PyUmi_send_docstring, py::arg("py_packet"),
            py::arg("blocking") = true)
        .def("recv", &PyUmi::recv, PyUmi_recv_docstring, py::arg("blocking") = true)
        .def("write", &PyUmi::write, PyUmi_write_docstring, py::arg("addr"), py::arg("data"),
            py::arg("srcaddr") = 0, py::arg("max_bytes") = 32, py::arg("posted") = false,
            py::arg("qos") = 0, py::arg("prot") = 0, py::arg("progressbar") = false,
            py::arg("error") = true)
        .def("read", &PyUmi::read, PyUmi_read_docstring, py::arg("addr"), py::arg("num"),
            py::arg("bytes_per_elem") = 1, py::arg("srcaddr") = 0, py::arg("max_bytes") = 32,
            py::arg("qos") = 0, py::arg("prot") = 0, py::arg("error") = true)
        .def("atomic", &PyUmi::atomic, PyUmi_atomic_docstring, py::arg("addr"), py::arg("data"),
            py::arg("opcode"), py::arg("srcaddr") = 0, py::arg("qos") = 0, py::arg("prot") = 0,
            py::arg("error") = true);

    m.def("umi_opcode_to_str", &umi_opcode_to_str,
        "Returns a string representation of a UMI opcode");

    m.def("delete_queue", &delete_queue, "Deletes an old queue.");
    m.def("delete_queues", &delete_queues, "Deletes a old queues specified in a list.");

    m.def("umi_pack", &umi_pack, "Returns a UMI command with the given parameters.",
        py::arg("opcode") = 0, py::arg("atype") = 0, py::arg("size") = 0, py::arg("len") = 0,
        py::arg("eom") = 1, py::arg("eof") = 1, py::arg("qos") = 0, py::arg("prot") = 0,
        py::arg("ex") = 0);

    m.def("umi_opcode", &umi_opcode);
    m.def("umi_size", &umi_size);
    m.def("umi_len", &umi_len);
    m.def("umi_atype", &umi_atype);
    m.def("umi_qos", &umi_qos);
    m.def("umi_prot", &umi_prot);
    m.def("umi_eom", &umi_eom);
    m.def("umi_eof", &umi_eof);
    m.def("umi_ex", &umi_ex);

    py::enum_<UMI_CMD>(m, "UmiCmd")
        .value("UMI_INVALID", UMI_INVALID)
        .value("UMI_REQ_READ", UMI_REQ_READ)
        .value("UMI_REQ_WRITE", UMI_REQ_WRITE)
        .value("UMI_REQ_POSTED", UMI_REQ_POSTED)
        .value("UMI_REQ_RDMA", UMI_REQ_RDMA)
        .value("UMI_REQ_ATOMIC", UMI_REQ_ATOMIC)
        .value("UMI_REQ_USER0", UMI_REQ_USER0)
        .value("UMI_REQ_FUTURE0", UMI_REQ_FUTURE0)
        .value("UMI_REQ_ERROR", UMI_REQ_ERROR)
        .value("UMI_REQ_LINK", UMI_REQ_LINK)
        .value("UMI_RESP_READ", UMI_RESP_READ)
        .value("UMI_RESP_WRITE", UMI_RESP_WRITE)
        .value("UMI_RESP_USER0", UMI_RESP_USER0)
        .value("UMI_RESP_USER1", UMI_RESP_USER1)
        .value("UMI_RESP_FUTURE0", UMI_RESP_FUTURE0)
        .value("UMI_RESP_FUTURE1", UMI_RESP_FUTURE1)
        .value("UMI_RESP_LINK", UMI_RESP_LINK)
        .export_values();

    py::enum_<UMI_ATOMIC>(m, "UmiAtomic")
        .value("UMI_REQ_ATOMICADD", UMI_REQ_ATOMICADD)
        .value("UMI_REQ_ATOMICAND", UMI_REQ_ATOMICAND)
        .value("UMI_REQ_ATOMICOR", UMI_REQ_ATOMICOR)
        .value("UMI_REQ_ATOMICXOR", UMI_REQ_ATOMICXOR)
        .value("UMI_REQ_ATOMICMAX", UMI_REQ_ATOMICMAX)
        .value("UMI_REQ_ATOMICMIN", UMI_REQ_ATOMICMIN)
        .value("UMI_REQ_ATOMICMAXU", UMI_REQ_ATOMICMAXU)
        .value("UMI_REQ_ATOMICMINU", UMI_REQ_ATOMICMINU)
        .value("UMI_REQ_ATOMICSWAP", UMI_REQ_ATOMICSWAP)
        .export_values();
}
