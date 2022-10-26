#include <stdint.h>
#include <cinttypes>
#include "switchboard.hpp"

int main() {
    SBTX tx;
    SBRX rx;

    int iterations=10;

    // initialize connections

    tx.init("queue-5555");
    rx.init("queue-5556");

    // initialize the packet
    sb_packet txp;
    sb_packet rxp;
    memset(&txp, 0, sizeof(txp));
    memset(&rxp, 0, sizeof(rxp));

    // loopback test
    
    uint64_t txcount = 0;
    uint64_t rxcount = 0;
    
    int exit_code = 0;

    while ((txcount < iterations) && (rxcount < iterations)) {
        if (tx.send(txp)) {
            // increment transmit counter
            txcount++;

            // update packet
            memcpy(txp.data, &txcount, sizeof(txcount));
        }
        if (rx.recv(rxp)) {
            // make sure that the packet is correct
            uint64_t tmp;
            memcpy(&tmp, rxp.data, sizeof(tmp));
            if (tmp != (rxcount + 42)) {
                printf("*** ERROR: data mismatch, got %" PRId64 " but expected %" PRId64 "\n", tmp, rxcount);
                exit_code = 1;
                break;
            }
         
            // increment the receive counter
            rxcount++;
        }
    }

    // send a packet that will end the test

    for (int i=0; i<32; i++) {
        txp.data[i] = 0xff;
    }
    tx.send_blocking(txp);

    // declare test as having passed or failed for regression testing purposes

    if (exit_code == 0) {
        printf("PASS!\n");
    } else {
        printf("FAIL\n");
    }

    return exit_code;
}
