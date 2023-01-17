/*
 * Python binding for Switchboard
 * Copyright (C) 2023 Zero ASIC
 */

#include <cstring>
#include <exception>
#include <memory>
#include <optional>
#include <stdexcept>
#include <stdio.h>
#include <iostream>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "bytesobject.h"
#include "object.h"
#include "pybind11/buffer_info.h"
#include "pybind11/detail/common.h"
#include "pybind11/pytypes.h"
#include "switchboard.hpp"
#include "umilib.hpp"

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

    PySbPacket(uint32_t destination=0, uint32_t flags=0,
        std::optional<py::array_t<uint8_t>> data = std::nullopt) :
        destination(destination), flags(flags) {
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

// As with PySbPacket, PyUmiPacket makes the contents of umi_packet
// accessible in a pybind-friendly manner.  The same comments about
// setting the default value of the data argument to "None" apply.

struct PyUmiPacket {
    PyUmiPacket(uint32_t opcode=0, uint32_t size=0, uint32_t user=0, uint64_t dstaddr=0,
        uint64_t srcaddr=0, std::optional<py::array_t<uint8_t>> data = std::nullopt) :
        opcode(opcode), size(size), user(user), dstaddr(dstaddr), srcaddr(srcaddr) {
        if (data.has_value()) {
            this->data = data.value();
        } else {
            this->data = py::array_t<uint8_t>(SB_DATA_SIZE);
        }
    }

    std::string toString() {
        std::stringstream stream;
        stream << "opcode: " << umi_opcode_to_str(opcode) << std::endl;
        stream << "size: " << size << std::endl;
        stream << "user: " << user << std::endl;
        stream << "dstaddr: 0x" << std::hex << dstaddr << std::endl;
        stream << "srcaddr: 0x" << std::hex << srcaddr << std::endl;
        stream << "data: " << py::str(data);
        return stream.str();
    }

    uint32_t opcode;
    uint32_t size;
    uint32_t user;
    uint64_t dstaddr;
    uint64_t srcaddr;
    py::array_t<uint8_t> data;
};

// check_signals() should be called within any loops where the C++
// code is waiting for something to happen.  this ensures that
// the binding doesn't hang after the user presses Ctrl-C.  the
// value "100000" is a balance between responsiveness and speed:
// setting it lower allows the binding to respond faster Ctrl-C,
// but incurs more overhead due to more frequent invocation of
// PyErr_CheckSignals().

void check_signals() {
    static int count = 0;

    if (count == 100000) {
        count = 0;
        if(PyErr_CheckSignals() != 0) {
            throw pybind11::error_already_set();
        }
    } else {
        count++;
    }
}

// highest_bit: determine the index of the most significant non-zero
// bit in a number.

size_t highest_bit (size_t x) {
    size_t retval = 0;
    while ((x>>=1) != 0) {
        retval++;
    }
    return retval;
}

// lowest_bit: determine index of the least significant non-zero
// bit in a number.

size_t lowest_bit (size_t x) {
    if (x == 0) {
        // if the input is zero, it is convenient to return a value
        // that is larger than the return value for any non-zero
        // input value, which is (sizeof(size_t)*8)-1.
        return sizeof(size_t)*8;
    } else {
        size_t retval = 0;
        while ((x & 1) == 0) {
            x >>= 1;
            retval++;
        }
        return retval;
    }
}

// PySbTx: pybind-friendly version of SBTX that works with PySbPacket

class PySbTx {
    public:
        PySbTx (std::string uri="") {
            init(uri);
        }

        void init(std::string uri) {
            if (uri != "") {
                m_tx.init(uri.c_str());
            }
        }

        bool send(const PySbPacket& py_packet, bool blocking=true) {
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
        PySbRx (std::string uri="") {
            init(uri);
        }

        void init(std::string uri) {
            if (uri != "") {
                m_rx.init(uri.c_str());
            }
        }

        std::unique_ptr<PySbPacket> recv(bool blocking=true) {
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

// PyUmi: Higher-level than PySbTx and PySbRx, this class works with two SB queues,
// one TX and one RX, to issue write requests and read requests according to the UMI
// specification.

class PyUmi {
    public:
        PyUmi (std::string tx_uri="", std::string rx_uri="") {
            init(tx_uri, rx_uri);
        }

        void init(std::string tx_uri, std::string rx_uri) {
            if (tx_uri != "") {
                m_tx.init(tx_uri.c_str());
            }
            if (rx_uri != "") {
                m_rx.init(rx_uri.c_str());
            }
        }

        std::unique_ptr<PyUmiPacket> recv(bool blocking=true) {
            // get a resposne

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

            // create an object to hold data to be returned to python
            std::unique_ptr<PyUmiPacket> resp(new PyUmiPacket());

            // parse the response
            py::buffer_info info = py::buffer(resp->data).request();
            umi_unpack((uint32_t*)p.data, resp->opcode, resp->size, resp->user,
                resp->dstaddr, resp->srcaddr, (uint8_t*)info.ptr, info.size);

            return resp;
        }

        void write(uint64_t addr, py::array_t<uint8_t> data) {
            // write data to the given address.  data can be of any length,
            // including greater than the length of a header packet and
            // values that are not powers of two.  this function is blocking.

            // get access to the data
            py::buffer_info info = py::buffer(data).request();

            // if there is nothing to write, return
            py::ssize_t num = info.size;
            if (num <= 0) {
                return;
            }

            // otherwise get the data pointer and decompose the data into
            // power-of-two chunks, with the size of each chunk being the
            // largest that is possible while remaining aligned, and
            // without exceeding the number of remaining bytes.

            uint8_t* ptr = (uint8_t*)info.ptr;

            while (num > 0) {
                // determine the largest aligned transaction that is possible
                ssize_t size = std::min(highest_bit(num), lowest_bit(addr));

                // perform a write of this size
                write_low_level(addr, ptr, size);

                // update indices
                num -= (1<<size);
                addr += (1<<size);
                ptr += (1<<size);
            }
        }

        py::array_t<uint8_t> read(uint64_t addr, size_t num, uint64_t srcaddr=0) {
            // read "num" bytes from the given address.  "num" may be any value,
            // including greater than the length of a header packet, and values
            // that are not powers of two.  the optional "srcaddr" argument is
            // the source address to which responses should be sent.  this
            // function is blocking.

            // create a buffer to hold the result
            py::array_t<uint8_t> result = py::array_t<uint8_t>(num);

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

            while (num > 0) {
                // determine the largest aligned transaction that is possible
                ssize_t size = std::min(highest_bit(num), lowest_bit(addr));

                // perform a read of this size
                read_low_level(addr, ptr, size, srcaddr);

                // update indices
                num -= (1<<size);
                addr += (1<<size);
                ptr += (1<<size);
            }

            return result;
        }

        py::array_t<uint8_t> atomic(uint64_t addr, py::array_t<uint8_t> data,
            uint32_t opcode, uint64_t srcaddr=0) {
            // apply an atomic operation at addr with input data

            // buffer for incoming data
            py::buffer_info in_info = py::buffer(data).request();
            py::ssize_t num = in_info.size;
            uint8_t* in_ptr = (uint8_t*)in_info.ptr;

            // buffer for outbound data
            py::array_t<uint8_t> result = py::array_t<uint8_t>(num);
            py::buffer_info out_info = py::buffer(result).request();
            uint8_t* out_ptr = (uint8_t*)out_info.ptr;

            if (num == 0) {
                // nothing to read, so just return the empty array
                return result;
            }

            size_t size = highest_bit(num);

            if (size > 4) {            
                throw std::runtime_error("Atomic operand must be 16 bytes or fewer to fit in a header packet.");
            }

            if (num != (1<<size)) {
                throw std::runtime_error("Width of atomic operand must be a power of two number of bytes.");
            }

            // perform the atomic operation

            read_low_level(addr, out_ptr, size, srcaddr, opcode, in_ptr);

            // return the result of the operation

            return result;
        }

    private:
        SBTX m_tx;
        SBRX m_rx;

        void write_low_level(uint64_t addr, uint8_t* ptr, uint32_t size) {
            sb_packet p;
            size_t flit_bytes = std::min(1<<size, 16);
            umi_pack((uint32_t*)(&p.data[0]), UMI_WRITE_POSTED, size, 0,
                addr, 0, ptr, flit_bytes);
            ptr += flit_bytes;

            // send the packet
            while (!m_tx.send(p)) {
                check_signals();
            }

            // send remaining packets if there are more to send
            if (size > 4) {
                size_t bytes_to_send = (1<<size) - 16;

                while (bytes_to_send > 0) {
                    // populate the next packet
                    size_t flit_bytes = std::min(bytes_to_send, (size_t)32);
                    umi_pack_burst((uint32_t*)p.data, ptr, flit_bytes);

                    // send the packet
                    while (!m_tx.send(p)) {
                        check_signals();
                    }

                    // increment the pointer, decrement bytes left to send
                    ptr += flit_bytes;
                    bytes_to_send -= flit_bytes;
                }
            }
        }

        void read_low_level(uint64_t addr, uint8_t* ptr, uint32_t size, uint64_t srcaddr,
            uint32_t opcode=UMI_READ_REQUEST, uint8_t* data=NULL) {

            // can handle both reads and atomic operations, since both involve a
            // request followed by a response packet or burst

            // create the packet
            sb_packet p;
            if (opcode == UMI_READ_REQUEST) {
                umi_pack((uint32_t*)p.data, opcode, size, 0, addr, srcaddr, NULL, 0);
            } else {
                umi_pack((uint32_t*)p.data, opcode, size, 0, addr, srcaddr, data, 1<<size);
            }

            // send the read request
            while (!m_tx.send(p)){
                check_signals();
            }

            // get the read response
            while (!m_rx.recv(p)) {
                check_signals();
            }

            // parse the response
            uint32_t resp_opcode, resp_size, resp_user;
            uint64_t resp_dstaddr, resp_srcaddr;
            size_t flit_bytes = std::min(1<<size, 16);
            umi_unpack((uint32_t*)p.data, resp_opcode, resp_size, resp_user,
                resp_dstaddr, resp_srcaddr, ptr, flit_bytes);
            ptr += flit_bytes;

            // check that the response makes sense
            if (!is_umi_write_response(resp_opcode)) {
                std::cerr << "Warning: got " << umi_opcode_to_str(resp_opcode)
                    << " in response to " << umi_opcode_to_str(opcode)
                    << " (expected WRITE-RESPONSE)" << std::endl;
            }
            if (resp_size != size) {
                std::cerr << "Warning: " << umi_opcode_to_str(opcode)
                    << " response size is " << std::to_string(resp_size)
                    << " (expected " << std::to_string(size) << ")" << std::endl;
            }
            if (resp_dstaddr != srcaddr) {
                std::cerr <<  "Warning: dstaddr in " << umi_opcode_to_str(opcode)
                    << " response is " << std::to_string(resp_dstaddr)
                    << " (expected " << std::to_string(srcaddr) << ")" << std::endl;
            }

            // receive remaining packets if this was part of a burst
            if (size > 4) {
                size_t bytes_to_recv = (1<<size) - 16;
                while (bytes_to_recv > 0) {
                    // get the next packet
                    while (!m_rx.recv(p)) {
                        check_signals();
                    }

                    // unpack the data
                    size_t flit_bytes = std::min(bytes_to_recv, (size_t)32);
                    umi_unpack_burst((uint32_t*)p.data, ptr, flit_bytes);

                    // increment the pointer, decrement bytes left to receive
                    ptr += flit_bytes;
                    bytes_to_recv -= flit_bytes;
                }
            }
        }
};

// convenience function to delete old queues from previous runs

void delete_queue(std::string uri) {
    delete_shared_queue(uri);
}

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
        .def(py::init<uint32_t, uint32_t, uint32_t, uint64_t, uint64_t,
            std::optional<py::array_t<uint8_t>>>(), py::arg("opcode") = 0,
            py::arg("size") = 0, py::arg("user") = 0, py::arg("dstaddr") = 0,
            py::arg("srcaddr") = 0, py::arg("data") = py::none())
        .def("__str__", &PyUmiPacket::toString)
        .def_readwrite("opcode", &PyUmiPacket::opcode)
        .def_readwrite("size", &PyUmiPacket::size)
        .def_readwrite("user", &PyUmiPacket::user)
        .def_readwrite("dstaddr", &PyUmiPacket::dstaddr)
        .def_readwrite("srcaddr", &PyUmiPacket::srcaddr)
        .def_readwrite("data", &PyUmiPacket::data);

    py::class_<PySbTx>(m, "PySbTx")
        .def(py::init<std::string>(), py::arg("uri") = "")
        .def("init", &PySbTx::init)
        .def("send", &PySbTx::send, py::arg("py_packet"), py::arg("blocking")=true);

    py::class_<PySbRx>(m, "PySbRx")
        .def(py::init<std::string>(), py::arg("uri") = "")
        .def("init", &PySbRx::init)
        .def("recv", &PySbRx::recv, py::arg("blocking")=true);

    py::class_<PyUmi>(m, "PyUmi")
        .def(py::init<std::string, std::string>(), py::arg("tx_uri") = "", py::arg("rx_uri") = "")
        .def("init", &PyUmi::init)
        .def("recv", &PyUmi::recv, py::arg("blocking")=true)
        .def("write", &PyUmi::write)
        .def("read", &PyUmi::read, py::arg("addr"), py::arg("num"), py::arg("srcaddr")=0)
        .def("atomic", &PyUmi::atomic, py::arg("addr"), py::arg("data"), py::arg("opcode"), py::arg("srcaddr")=0);

    m.def("umi_opcode_to_str", &umi_opcode_to_str, "Returns a string representation of a UMI opcode");

    m.def("delete_queue", &delete_queue, "Deletes an old queue.");

    py::enum_<UMI_CMD>(m, "UmiCmd")
        .value("UMI_INVALID", UMI_INVALID)
        .value("UMI_WRITE_POSTED", UMI_WRITE_POSTED)
        .value("UMI_WRITE_RESPONSE", UMI_WRITE_RESPONSE)
        .value("UMI_WRITE_SIGNAL", UMI_WRITE_SIGNAL)
        .value("UMI_WRITE_STREAM", UMI_WRITE_STREAM)
        .value("UMI_WRITE_ACK", UMI_WRITE_ACK)
        .value("UMI_READ_REQUEST", UMI_READ_REQUEST)
        .value("UMI_ATOMIC_ADD", UMI_ATOMIC_ADD)
        .value("UMI_ATOMIC_AND", UMI_ATOMIC_AND)
        .value("UMI_ATOMIC_OR", UMI_ATOMIC_OR)
        .value("UMI_ATOMIC_XOR", UMI_ATOMIC_XOR)
        .value("UMI_ATOMIC_MAX", UMI_ATOMIC_MAX)
        .value("UMI_ATOMIC_MIN", UMI_ATOMIC_MIN)
        .value("UMI_ATOMIC_MAXU", UMI_ATOMIC_MAXU)
        .value("UMI_ATOMIC_MINU", UMI_ATOMIC_MINU)
        .value("UMI_ATOMIC_SWAP", UMI_ATOMIC_SWAP)
        .value("UMI_ATOMIC", UMI_ATOMIC)
        .export_values();

}
