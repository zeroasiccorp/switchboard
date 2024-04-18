// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <cstdlib>
#include <iostream>
#include <map>
#include <memory>
#include <thread>
#include <vector>

#include "switchboard.hpp"

// connections to each of the entries in the grid
std::map<int, int> routing_table;
std::map<int, std::unique_ptr<SBTX>> txconn;
std::vector<std::unique_ptr<SBRX>> rxconn;

bool init(int argc, char* argv[]) {
    // determine number of rows and columns

    int arg_idx = 1;

    enum MODE { RX, TX, ROUTE, UNDEF };
    MODE mode = UNDEF;

    while (arg_idx < argc) {
        std::string arg = std::string(argv[arg_idx++]);
        if (arg == "--rx") {
            mode = RX;
        } else if (arg == "--tx") {
            mode = TX;
        } else if (arg == "--route") {
            mode = ROUTE;
        } else if (mode == RX) {
            rxconn.push_back(std::unique_ptr<SBRX>(new SBRX()));
            rxconn.back()->init(std::string("queue-") + arg);
        } else if (mode == TX) {
            int queue = atoi(arg.c_str());
            txconn[queue] = std::unique_ptr<SBTX>(new SBTX());
            txconn[queue]->init(std::string("queue-") + arg);
        } else if (mode == ROUTE) {
            size_t split = arg.find(':');
            std::string first = arg.substr(0, split);
            std::string second = arg.substr(split + 1);
            int dest = atoi(first.c_str());
            int queue = atoi(second.c_str());
            routing_table[dest] = queue;
        } else {
            return false;
        }
    }

    return true;
}

int main(int argc, char* argv[]) {
    // set up connections
    if (!init(argc, argv)) {
        printf("ERROR: arguments are not formed properly.\n");
        return 1;
    }

    sb_packet p;
    while (true) {
        // loop over all RX connection
        for (auto& rx : rxconn) {
            if (rx->is_active()) {
                if (rx->recv_peek(p)) {
                    // make sure that the destination is in the routing table and active
                    if ((routing_table.count(p.destination) > 0) &&
                        (txconn.count(routing_table[p.destination]) > 0) &&
                        (txconn[routing_table[p.destination]]->is_active())) {

                        // try to send the packet, removing it from
                        // the RX queue if the send is successful
                        if (txconn[routing_table[p.destination]]->send(p)) {
                            rx->recv();
                        }
                    } else {
                        printf("ERROR: Cannot route packet.\n");
                        return 1;
                    }
                }
            }
        }
    }

    return 0;
}
