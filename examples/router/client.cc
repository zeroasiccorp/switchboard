// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "switchboard.hpp"

#define NBYTES 32

int main() {
    SBTX tx;
    SBRX rx;

    // initialize connections

    tx.init("queue-5555");
    rx.init("queue-5556");

    // form packet

    sb_packet txp;

    for (int i = 0; i < NBYTES; i++) {
        txp.data[i] = i & 0xff;
    }

    txp.destination = 1;
    txp.last = true;

    // send packet

    tx.send_blocking(txp);
    printf("TX packet: %s\n", sb_packet_to_str(txp, NBYTES).c_str());

    // receive packet

    sb_packet rxp;

    rx.recv_blocking(rxp);
    printf("RX packet: %s\n", sb_packet_to_str(rxp, NBYTES).c_str());

    for (int i = 0; i < NBYTES; i++) {
        assert(rxp.data[i] == (txp.data[i] + 1));
    }

    // declare test as having passed for regression testing purposes

    printf("PASS!\n");

    return 0;
}
