#include <cstring>
#include <memory>
#include <stdio.h>
#include <iostream>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "switchboard.hpp"
#include "umilib.hpp"

namespace py = pybind11;

struct PySbPacket {
    PySbPacket() {}
    uint32_t destination;
    uint32_t flags;
    std::array<uint8_t, SB_DATA_SIZE> data;
 };

struct PyUmiPacket {
    PyUmiPacket() {}

    uint32_t opcode;
    uint32_t size;
    uint32_t user;
    uint64_t dstaddr;
    uint64_t srcaddr;
    std::array<uint8_t, 32> data;
};

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

class PyUmi {
    public:
        PyUmi () {}

        void init(std::string tx_uri, std::string rx_uri) {
            if (tx_uri != "") {
                m_tx.init(tx_uri.c_str());
            }
            if (rx_uri != "") {
                m_rx.init(rx_uri.c_str());
            }
        }

        void write(PyUmiPacket& umi) {
            // form the UMI packet
            sb_packet p;
            umi_pack((uint32_t*)(&p.data[0]), UMI_WRITE_POSTED, umi.size,
                0, umi.dstaddr, 0, &umi.data[0], 1<<umi.size);

            // send the packet
            while(!m_tx.send(p)){
                check_signals();
            }
        }

        void read(PyUmiPacket& umi, uint64_t srcrow, uint64_t srccol) {
            // compute the source address
            uint64_t rdsrcaddr = 0;
            rdsrcaddr |= (srcrow & 0xff) << 48;
            rdsrcaddr |= (srccol & 0xff) << 40;

            // determine the size of the transaction
            uint32_t rdsize = umi.size;

            // form the UMI packet
            sb_packet p;
            umi_pack((uint32_t*)p.data, UMI_READ_REQUEST, rdsize, 0, umi.dstaddr, rdsrcaddr, NULL, 0);

            // send the packet
            while(!m_tx.send(p)){
                check_signals();
            }

            // receive the response
            while(!m_rx.recv(p)) {
                check_signals();
            }

            // parse the response
            umi_unpack((uint32_t*)p.data, umi.opcode, umi.size, umi.user, umi.dstaddr,
                umi.srcaddr, &umi.data[0], 1<<rdsize);

            // check that the response makes sense
            if (!is_umi_write_response(umi.opcode)) {
                std::string err_msg = "";
                err_msg += "Warning: got ";
                err_msg += umi_opcode_to_str(umi.opcode);
                err_msg += " in response to a READ (expected WRITE-RESPONSE)";
                std::cerr << err_msg << std::endl;
            }
            if (umi.size != rdsize) {
                std::string err_msg = "";
                err_msg += "Warning: read response size is ";
                err_msg += std::to_string(umi.size);
                err_msg += " (expected ";
                err_msg += std::to_string(rdsize);
                err_msg += ")";
                std::cerr << err_msg << std::endl;
            }
            if (umi.dstaddr != rdsrcaddr) {
                std::string err_msg = "";
                err_msg += "Warning: dstaddr in read response is ";
                err_msg += std::to_string(umi.dstaddr);
                err_msg += " (expected ";
                err_msg += std::to_string(rdsrcaddr);
                err_msg += ")";
                std::cerr << err_msg << std::endl;
            }
        }

    private:
        SBTX m_tx;
        SBRX m_rx;
};

class PySbTx {
    public:
        PySbTx () {}

        void init(std::string uri) {
            m_tx.init(uri.c_str());
        }

        bool send(PySbPacket& py_packet) {
            // TODO: try to avoid copying data

            sb_packet p;
            p.destination = py_packet.destination;
            p.flags = py_packet.flags;
            memcpy(p.data, &py_packet.data[0], SB_DATA_SIZE);

            return m_tx.send(p);
        }
    private:
        SBTX m_tx;
};

class PySbRx {
    public:
        PySbRx () {}

        void init(std::string uri) {
            m_rx.init(uri.c_str());
        }

        bool recv(PySbPacket& py_packet) {
            // TODO: try to avoid copying data

            sb_packet p;
            if (m_rx.recv(p)){
                // convert data format
                py_packet.destination = p.destination;
                py_packet.flags = p.flags;
                memcpy(&py_packet.data[0], p.data, SB_DATA_SIZE);

                // indicate data was received
                return true;
            } else {
                // indicate no data was received
                return false;
            }
        }
    private:
        SBRX m_rx;
};

void delete_queue(std::string uri) {
    delete_shared_queue(uri);
}

void hello_world() {
    // just for testing purposes
    printf("Hello World!\n");
}

PYBIND11_MODULE(_switchboard, m) {
    m.doc() = "switchboard pybind11 plugin";

    py::class_<PySbPacket>(m, "PySbPacket")
        .def(py::init<>())
        .def_readwrite("destination", &PySbPacket::destination)
        .def_readwrite("flags", &PySbPacket::flags)
        .def_readwrite("data", &PySbPacket::data);

    py::class_<PyUmiPacket>(m, "PyUmiPacket")
        .def(py::init<>())
        .def_readwrite("opcode", &PyUmiPacket::opcode)
        .def_readwrite("size", &PyUmiPacket::size)
        .def_readwrite("user", &PyUmiPacket::user)
        .def_readwrite("dstaddr", &PyUmiPacket::dstaddr)
        .def_readwrite("srcaddr", &PyUmiPacket::srcaddr)
        .def_readwrite("data", &PyUmiPacket::data);

    py::class_<PySbTx>(m, "PySbTx")
        .def(py::init<>())
        .def("init", &PySbTx::init)
        .def("send", &PySbTx::send);

    py::class_<PySbRx>(m, "PySbRx")
        .def(py::init<>())
        .def("init", &PySbRx::init)
        .def("recv", &PySbRx::recv);

    py::class_<PyUmi>(m, "PyUmi")
        .def(py::init<>())
        .def("init", &PyUmi::init)
        .def("write", &PyUmi::write)
        .def("read", &PyUmi::read);

    m.def("umi_opcode_to_str", &umi_opcode_to_str, "Returns a string representation of a UMI opcode");

    m.def("delete_queue", &delete_queue, "Deletes an old queue.");

    m.def("hello_world", &hello_world, "Print a message for testing purposes.");
}
