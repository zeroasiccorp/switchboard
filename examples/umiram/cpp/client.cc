#include "switchboard.hpp"
#include "umilib.hpp"

void print_packet_details(const uint32_t* p) {
    uint32_t opcode, size, user;
    uint64_t dstaddr, srcaddr;
    uint32_t data_arr[4];
    umi_unpack(p, opcode, size, user, dstaddr, srcaddr, (uint8_t*)data_arr, 16);

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

    // initialize tx connection
    SBTX stop;
    stop.init("queue-5557");

    // packet structure used for sending/receiving
    sb_packet p;

    // write 0xBEEFCAFE to address 0x12
    uint32_t val = 0xBEEFCAFE;
    umi_pack((uint32_t*)p.data, UMI_WRITE_POSTED, 2, 0, 0x12, 0, (uint8_t*)(&val), 4);
    tx.send_blocking(p);
    printf("TX packet: %s\n", umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);
    printf("\n");

    // send request to read address 0x12 into address 0x34
    umi_pack((uint32_t*)p.data, UMI_READ_REQUEST, 2, 0, 0x12, 0x34, NULL, 0);
    tx.send_blocking(p);
    printf("TX packet: %s\n", umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);
    printf("\n");

    // receive read response
    rx.recv_blocking(p);
    printf("RX packet: %s\n", umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);

    // stop simulation
    stop.send_blocking(p);

    return 0;
}
