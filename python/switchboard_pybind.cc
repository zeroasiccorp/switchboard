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
#include "switchboard_pcie.hpp"
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
        return umi_transaction_as_str<PyUmiPacket>(*this);
    }

    void resize(size_t n) {
        data = py::array_t<uint8_t>(n);
    }

    size_t len(){
        py::buffer_info info = py::buffer(data).request();
        return info.size;
    }

    uint8_t* ptr() {
        py::buffer_info info = py::buffer(data).request();
        return (uint8_t*)info.ptr;        
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

// functions for allocating and accessing the pointer to pybind arrays

py::array_t<uint8_t> alloc_pybind_array(int n) {
    return py::array_t<uint8_t>(n);
}

uint8_t* get_pybind_array_ptr(py::array_t<uint8_t> arr) {
    py::buffer_info info = py::buffer(arr).request();
    return (uint8_t*)info.ptr;
}

// PySbTxPcie / PySbRxPcie: these objects must be created to initialize Switchboard
// queues that are accessed over PCIe.  Care must be taken to ensure that they
// don't go out of scope, since that will invoke destructors that deinitialize
// the queues.

struct PySbTxPcie {
    PySbTxPcie (std::string uri="", int idx=0, int bar_num=0, std::string bdf="") {
        init(uri, idx, bar_num, bdf);
    }

    void init(std::string uri="", int idx=0, int bar_num=0, std::string bdf="") {
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
    PySbRxPcie (std::string uri="", int idx=0, int bar_num=0, std::string bdf="") {
        init(uri, idx, bar_num, bdf);
    }

    void init(std::string uri="", int idx=0, int bar_num=0, std::string bdf="") {
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

// Functions to show a progress bar.

static void progressbar_show(uint64_t progress, uint64_t total) {
    unsigned int progress_percent = progress * 100 / total;
    // Cap it to 50 chars for smaller terminals.
    unsigned int count = progress_percent / 2;

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

        bool send(PyUmiPacket& py_packet, bool blocking=true) {
            // sends (or tries to send, if blocking=false) a single UMI transaction
            // if length of the data payload in the packet is greater than
            // what can be sent in a header packet, then a header packet is sent
            // containing the beginning of the data, followed by the rest in
            // subsequent burst packets.

            return umisb_send<PyUmiPacket>(py_packet, m_tx, blocking, &check_signals);
        } 

        std::unique_ptr<PyUmiPacket> recv(bool blocking=true) {
            // try to receive a transaction
            std::unique_ptr<PyUmiPacket> resp = std::unique_ptr<PyUmiPacket>(
                new PyUmiPacket(0, 0, 0, 0, 0, py::array_t<uint8_t>(0)));
            bool success = umisb_recv<PyUmiPacket>(*resp.get(), m_rx, blocking, &check_signals);

            // if we got something, return it, otherwise return a null pointer
            if (success) {
                return resp;
            } else {
                return nullptr;
            }
        }

        void write(uint64_t addr, py::array_t<uint8_t> data, uint32_t max_size=15, bool progressbar=false) {
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
                size = std::min(size, (ssize_t)max_size);

                // perform a write of this size
                UmiTransaction x(UMI_WRITE_POSTED, size, 0, addr, 0, ptr, 1<<size);
                umisb_send<UmiTransaction>(x, m_tx, true, &check_signals);

                // update indices
                num -= (1<<size);
                addr += (1<<size);
                ptr += (1<<size);

                if (progressbar) {
                    uint64_t progress = info.size - num;
                    progressbar_show(progress, info.size);
                }
            }
            if (progressbar) {
                progressbar_done();
            }
        }

        py::array_t<uint8_t> read(uint64_t addr, size_t num, uint64_t srcaddr=0,
            uint32_t max_size=15) {

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
                size = std::min(size, (ssize_t)max_size);

                // read request
                UmiTransaction request(UMI_READ_REQUEST, size, 0, addr, srcaddr, NULL, 0);
                umisb_send<UmiTransaction>(request, m_tx, true, &check_signals);

                // get response
                UmiTransaction reply(0, 0, 0, 0, 0, ptr, 1<<size);
                umisb_recv<UmiTransaction>(reply, m_rx, true, &check_signals);

                // check that the reply makes sense
                umisb_check_reply<UmiTransaction>(request, reply);

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

            // create outbound packet

            PyUmiPacket request(opcode, 0, 0, addr, srcaddr, data);
            size_t num = request.len();

            if (num == 0) {
                // nothing to read, so just return the empty array
                return py::array_t<uint8_t>(0);
            }

            // if we get to this point, there is a transaction of non-zero size

            // calculate the size of the transaction

            request.size = highest_bit(num); 

            if (request.size > 4) {
                throw std::runtime_error("Atomic operand must be 16 bytes or fewer to fit in a header packet.");
            }

            if (num != (1<<request.size)) {
                throw std::runtime_error("Width of atomic operand must be a power of two number of bytes.");
            }

            // send the request

            umisb_send<PyUmiPacket>(request, m_tx, true, &check_signals);

            // get the reply

            PyUmiPacket reply;
            umisb_recv<PyUmiPacket>(reply, m_rx, true, &check_signals);

            // check that the reply makes sense

            umisb_check_reply<PyUmiPacket>(request, reply);

            // return the result of the operation

            return reply.data;
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
        .def(py::init<std::string, std::string>(), py::arg("tx_uri") = "", py::arg("rx_uri") = "")
        .def("init", &PyUmi::init)
        .def("send", &PyUmi::send, py::arg("py_packet"), py::arg("blocking")=true)
        .def("recv", &PyUmi::recv, py::arg("blocking")=true)
        .def("write", &PyUmi::write, py::arg("addr"), py::arg("data"), py::arg("max_size")=15, py::arg("progressbar")=false)
        .def("read", &PyUmi::read, py::arg("addr"), py::arg("num"), py::arg("srcaddr")=0, py::arg("max_size")=15)
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
