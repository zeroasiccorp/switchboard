#include "switchboard.hpp"

int main() {
    SBTX tx;
    SBRX rx;
    
    // initialize connections
    tx.init("queue-5555");
    rx.init("queue-5556");

    // send packet
    sb_packet txp;

    txp.destination = 0xbeefcafe;
    txp.last = 0;
    for (int i=0; i<32; i++) {
        txp.data[i] = i & 0xff;
    }
    
    tx.send_blocking(txp);
    printf("TX packet: %s\n", sb_packet_to_str(txp).c_str());

    // receive packet
    sb_packet rxp;

    rx.recv_blocking(rxp);

    printf("RX packet: %s\n", sb_packet_to_str(rxp).c_str());

    for (int i=0; i<32; i++) {
        assert(rxp.data[i] == (txp.data[i] + 1));
    }

    return 0;
}
