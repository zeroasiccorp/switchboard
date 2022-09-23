#include "switchboard.hpp"
#include "umilib.hpp"

void print_packet_details(const uint32_t* p) {
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
    SBTX tx;
    tx.init("queue-5555");

    // initialize rx connection
    SBRX rx;
    rx.init("queue-5556");

    // packet structure used for sending/receiving
    sb_packet p;

    // write 0xBEEFCAFE to address 0x12
    umi_pack((uint32_t*)p.data, UMI_WRITE_NORMAL, 0x12, 0, (uint32_t)0xBEEFCAFE);
    tx.send_blocking(p);
    printf("TX packet: %s\n", umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);
    printf("\n");

    // send request to read address 0x12 into address 0x34
    umi_pack((uint32_t*)p.data, UMI_READ, 0x12, 0x34, (uint32_t)0);
    tx.send_blocking(p);
    printf("TX packet: %s\n", umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);
    printf("\n");

    // receive read request
    rx.recv_blocking(p);
    printf("RX packet: %s\n", umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);

    return 0;
}
