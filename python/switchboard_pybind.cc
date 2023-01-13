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
#include <sys/_types/_size_t.h>

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

// highest_bit: determine the highest bit in a number.  useful for
// splitting apart data into power-of-two chunks.

size_t highest_bit (size_t x) {
    size_t retval = 0;
    while ((x>>=1) != 0) {
        retval++;
    }
    return retval;
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
            // power-of-two chunks, sending them out from largest to smallest.
            // it seems that this would probably be better than smallest to
            // largest, to avoid forcing large transfers to be unaligned when
            // they would necessarily have to be (e.g., a power-of-two chunk
            // with an extra byte on the end)
            
            // TODO: use burst mode instead of all header packets, noting that
            // there may have to be multiple bursts if the amount of data to be
            // transferred is not a power of two.

            uint8_t* ptr = (uint8_t*)info.ptr;

            size_t max_size = highest_bit(num);

            for (ssize_t size=max_size; size>=0; size--) {
                if (((num >> size) & 1) == 0) {
                    // skip if there is no chunk that needs to
                    // be transmitted at this size
                    continue;
                }

                // construct a packet
                sb_packet p;
                umi_pack((uint32_t*)(&p.data[0]), UMI_WRITE_POSTED, size, 0,
                    addr, 0, ptr, SB_DATA_SIZE);

                // send the packet
                while (!m_tx.send(p)) {
                    check_signals();
                }

                // update write address and data pointer
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

            // otherwise get the data pointer and decompose the data into
            // power-of-two chunks, reading them in from largest to smallest,
            // as was done for writing

            // TODO: use burst mode instead of all header packets, noting that
            // there may have to be multiple bursts if the amount of data to be
            // transferred is not a power of two.

            py::buffer_info info = py::buffer(result).request();
            uint8_t* ptr = (uint8_t*)info.ptr;

            size_t max_size = highest_bit(num);

            for (ssize_t size=max_size; size>=0; size--) {
                if (((num>>size) & 1) == 0) {
                    // skip if there is no chunk that needs to
                    // be read at this size
                    continue;
                }

                // create the packet
                sb_packet p;
                umi_pack((uint32_t*)p.data, UMI_READ_REQUEST, size, 0,
                    addr, srcaddr, NULL, 0);

                // send the read request
                while(!m_tx.send(p)){
                    check_signals();
                }

                // get the read response
                while(!m_rx.recv(p)) {
                    check_signals();
                }

                // parse the response
                uint32_t resp_opcode, resp_size, resp_user;
                uint64_t resp_dstaddr, resp_srcaddr;
                umi_unpack((uint32_t*)p.data, resp_opcode, resp_size, resp_user,
                    resp_dstaddr, resp_srcaddr, ptr, 1<<size);

                // check that the response makes sense
                if (!is_umi_write_response(resp_opcode)) {
                    std::cerr << "Warning: got " << umi_opcode_to_str(resp_opcode)
                        << " in response to a READ (expected WRITE-RESPONSE)" << std::endl;
                }
                if (resp_size != size) {
                    std::cerr << "Warning: read response size is " << std::to_string(resp_size)
                        << " (expected " << std::to_string(size) << ")" << std::endl;
                }
                if (resp_dstaddr != srcaddr) {
                    std::cerr <<  "Warning: dstaddr in read response is " << std::to_string(resp_dstaddr)
                        << " (expected " << std::to_string(srcaddr) << ")" << std::endl;
                }

                // update address and pointer
                addr += (1<<size);
                ptr += (1<<size);
            }

            return result;
        }

    private:
        SBTX m_tx;
        SBRX m_rx;
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
        .def("write", &PyUmi::write)
        .def("read", &PyUmi::read, py::arg("addr"), py::arg("num"), py::arg("srcaddr")=0);

    m.def("umi_opcode_to_str", &umi_opcode_to_str, "Returns a string representation of a UMI opcode");

    m.def("delete_queue", &delete_queue, "Deletes an old queue.");
}
