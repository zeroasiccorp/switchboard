// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "switchboard.hpp"
#include <cinttypes>
#include <stdint.h>

int main() {
    SBTX tx;
    SBRX rx;

    int iterations = 10;

    // initialize connections

    tx.init("in.q");
    rx.init("out.q");

    // initialize the packet
    sb_packet txp;
    sb_packet rxp;
    memset(&txp, 0, sizeof(txp));
    memset(&rxp, 0, sizeof(rxp));

    // loopback test

    uint64_t txcount = 0;
    uint64_t rxcount = 0;

    int success = 1;

    while ((txcount < iterations) || (rxcount < iterations)) {
        if ((txcount < iterations) && tx.send(txp)) {
            // increment transmit counter
            txcount++;

            // update packet
            memcpy(txp.data, &txcount, sizeof(txcount));
        }
        if ((rxcount < iterations) && rx.recv(rxp)) {
            // make sure that the packet is correct
            uint64_t tmp;
            memcpy(&tmp, rxp.data, sizeof(tmp));

            uint64_t expected = rxcount + 0x0101010101010101;

            if (tmp != expected) {
                printf("*** ERROR: data mismatch, got %" PRId64 " but expected %" PRId64 "\n", tmp,
                    expected);
                success = 0;
            }

            rxcount++;
        }
    }

    // declare test as having passed or failed for regression testing purposes

    if (success) {
        printf("PASS!\n");
        return 0;
    } else {
        printf("FAIL\n");
        return 1;
    }
}
