// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "switchboard.hpp"

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

    const char* arg = "5555";
    if (arg_idx < argc) {
        arg = argv[arg_idx++];
    }
    char port[128];
    sprintf(port, "queue-%s", arg);

    if (is_tx) {
        SBTX tx;
        tx.init(port);

        // form packet with an interesting pattern
        sb_packet p;
        p.destination = 0xbeefcafe;
        p.last = true;
        for (int i = 0; i < NBYTES; i++) {
            p.data[i] = 0;
            for (int j = 0; j < 2; j++) {
                p.data[i] <<= 4;
                p.data[i] |= (i + j) % 16;
            }
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
    }

    return 0;
}
