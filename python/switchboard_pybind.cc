#include <cstring>
#include <memory>
#include <stdio.h>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "switchboard.hpp"
#include "umilib.hpp"

namespace py = pybind11;

static std::vector<std::unique_ptr<SBRX>> rx_vec;
static std::vector<std::unique_ptr<SBTX>> tx_vec;

struct PySbPacket {
    PySbPacket() {}
    uint32_t destination;
    uint32_t flags;
    std::array<uint8_t, SB_DATA_SIZE> data;
 };

void delete_queue(std::string uri) {
    delete_shared_queue(uri);
}

int init_rx(std::string uri) {
    rx_vec.push_back(std::unique_ptr<SBRX>(new SBRX));
    rx_vec.back()->init(uri);
    return (rx_vec.size() - 1);
}

int init_tx(std::string uri) {
    tx_vec.push_back(std::unique_ptr<SBTX>(new SBTX));
    tx_vec.back()->init(uri);
    return (tx_vec.size() - 1);
}

bool sb_send(int id, PySbPacket& py_packet) {
    // TODO: clean this up, try to avoid copying if not needed
    
    // convert data format
    sb_packet p;
    p.destination = py_packet.destination;
    p.flags = py_packet.flags;
    memcpy(p.data, &py_packet.data[0], SB_DATA_SIZE);

    // send the data
    return tx_vec[id]->send(p);
}

bool sb_recv(int id, PySbPacket& py_packet) {
    // TODO: clean up, try to avoid copying data if not needed

    sb_packet p;
    if (rx_vec[id]->recv(p)){
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

void hello_world() {
    // just for testing purposes
    printf("Hello World!\n");
}

PYBIND11_MODULE(switchboard_pybind, m) {
    m.doc() = "switchboard_pybind plugin";
    m.def("delete_queue", &delete_queue, "Deletes an old queue.");
    m.def("init_rx", &init_rx, "Initializes queue for receiving data.");
    m.def("init_tx", &init_tx, "Initializes queue for transmitting data.");
    m.def("sb_recv", &sb_recv, "Receives a Switchboard packet.");
    m.def("sb_send", &sb_send, "Sends a Switchboard packet.");
    m.def("hello_world", &hello_world, "Print a message for testing purposes.");
    py::class_<PySbPacket>(m, "PySbPacket")
        .def(py::init<>())
        .def_readwrite("destination", &PySbPacket::destination)
        .def_readwrite("flags", &PySbPacket::flags)
        .def_readwrite("data", &PySbPacket::data);
}
