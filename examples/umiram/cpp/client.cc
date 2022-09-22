#include "switchboard.hpp"

void print_packet_details(const umi_packet& p) {
    uint32_t opcode, size, user;
    uint64_t dstaddr, srcaddr;
    uint32_t data_arr[4];
    umi_unpack(p, opcode, size, user, dstaddr, srcaddr, data_arr);

    // print details
    printf("opcode:  %s\n", umi_opcode_to_str(opcode).c_str());
    printf("dstaddr: 0x%016llx\n", dstaddr);
    printf("size:    %u\n", size);
    printf("data:    0x%08x\n", data_arr[0]);
}

int main() {
    // initialize tx connection
    UmiConnection tx;
    tx.init("queue-5555", true, true);

    // initialize rx connection
    UmiConnection rx;
    rx.init("queue-5556", false, true);

    // packet structure used for sending/receiving
    umi_packet p;

    // write 0xBEEFCAFE to address 0x12
    umi_pack(p, UMI_WRITE_NORMAL, 0x12, 0, (uint32_t)0xBEEFCAFE);
    tx.send_blocking(p);
    printf("TX packet: %s\n", umi_packet_to_str(p).c_str());
    print_packet_details(p);
    printf("\n");

    // send request to read address 0x12 into address 0x34
    umi_pack(p, UMI_READ, 0x12, 0x34, (uint32_t)0);
    tx.send_blocking(p);
    printf("TX packet: %s\n", umi_packet_to_str(p).c_str());
    print_packet_details(p);
    printf("\n");

    // receive read request
    rx.recv_blocking(p);
    printf("RX packet: %s\n", umi_packet_to_str(p).c_str());
    print_packet_details(p);

    return 0;
}
