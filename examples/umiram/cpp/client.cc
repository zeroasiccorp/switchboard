#include "switchboard.hpp"

int main() {
    // initialize tx connection
    UmiConnection tx;
    tx.init("queue-5555", true, true);

    // initialize rx connection
    UmiConnection rx;
    rx.init("queue-5556", false, true);

    // variables for packet formation
    umi_packet p;
    uint32_t dstaddr[2];
    uint32_t srcaddr[2];
    uint32_t data[8];

    // send write packet
    memset(dstaddr, 0, sizeof(dstaddr));
    memset(srcaddr, 0, sizeof(srcaddr));
    memset(data, 0, sizeof(data));
    dstaddr[0] = 12;
    data[0] = 0xBEEFCAFE;
    umi_pack(p, UMI_WRITE_NORMAL, 5, 0, dstaddr, srcaddr, data);
    tx.send_blocking(p);
    printf("Sent packet: %s\n", umi_packet_to_str(p).c_str());
    
    // send read request
    memset(dstaddr, 0, sizeof(dstaddr));
    memset(srcaddr, 0, sizeof(srcaddr));
    memset(data, 0, sizeof(data));
    dstaddr[0] = 12;
    srcaddr[0] = 32;
    umi_pack(p, UMI_READ, 5, 0, dstaddr, srcaddr, data);
    tx.send_blocking(p);
    printf("Sent packet: %s\n", umi_packet_to_str(p).c_str());

    // receive read request
    rx.recv_blocking(p);
    printf("Received packet: %s\n", umi_packet_to_str(p).c_str());

    return 0;
}
