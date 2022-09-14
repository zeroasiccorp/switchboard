#include "switchboard.hpp"

int main() {
    UmiConnection tx;
    UmiConnection rx;
    umi_packet txp = {0};
    umi_packet rxp = {0};
    
    // initialize connections
    tx.init("queue-5555", true, true);
    rx.init("queue-5556", false, true);

    // send packet
    for (int i=0; i<8; i++) {
        txp[i] = i;
    }
    tx.send_blocking(txp);
    printf("Sent packet: %s\n", umi_packet_to_str(txp).c_str());

    // receive packet
    rx.recv_blocking(rxp);
    printf("Received packet: %s\n", umi_packet_to_str(rxp).c_str());

    return 0;
}
