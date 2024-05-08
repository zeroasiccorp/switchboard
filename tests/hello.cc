// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "switchboard.hpp"
#include <stdexcept>

#define NBYTES 32

// example usage

int main(int argc, char* argv[]) {
    int arg_idx = 1;

    // determine if this is TX or RX

    bool is_tx = false;
    if (arg_idx < argc) {
        const char* arg = argv[arg_idx++];
        if (strcmp(arg, "-") == 0) {
            // use default
        } else if (strcmp(arg, "tx") == 0) {
            is_tx = true;
        } else if (strcmp(arg, "rx") == 0) {
            is_tx = false;
        } else {
            fprintf(stderr, "Unknown argument: %s\n", arg);
            exit(1);
        }
    }

    // determine the communication port to use

    const char* port = "queue-0";
    if (arg_idx < argc) {
        port = argv[arg_idx++];
    }

    if (is_tx) {
        SBTX tx;
        tx.init(port);

        // form packet with an interesting pattern
        sb_packet p;
        p.destination = 0xbeefcafe;
        p.last = true;
        for (int i = 0; i < NBYTES; i++) {
            p.data[i] = i;
        }

        // send packet
        tx.send_blocking(p);
    } else {
        SBRX rx;
        rx.init(port);

        // receive packet
        sb_packet p;
        rx.recv_blocking(p);

        // print packet
        printf("%s\n", sb_packet_to_str(p, NBYTES).c_str());

        // check destination
        if (p.destination != 0xbeefcafe) {
            throw std::runtime_error("MISMATCH");
        }

        // check data
        for (int i = 0; i < NBYTES; i++) {
            if (p.data[i] != i) {
                throw std::runtime_error("MISMATCH");
            }
        }
    }

    return 0;
}
