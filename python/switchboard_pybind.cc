#include <cstring>
#include <memory>
#include <stdio.h>

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

    py::class_<PySbTx>(m, "PySbTx")
        .def(py::init<>())
        .def("init", &PySbTx::init)
        .def("send", &PySbTx::send);

    py::class_<PySbRx>(m, "PySbRx")
        .def(py::init<>())
        .def("init", &PySbRx::init)
        .def("recv", &PySbRx::recv);

    m.def("delete_queue", &delete_queue, "Deletes an old queue.");

    m.def("hello_world", &hello_world, "Print a message for testing purposes.");
}
