#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>

#include "switchboard.hpp"
#include "old_umilib.hpp"

void print_packet_details(const uint32_t* p) {
    uint32_t opcode, size, user;
    uint64_t dstaddr, srcaddr;
    uint32_t data_arr[4];
    old_umi_unpack(p, opcode, size, user, dstaddr, srcaddr, (uint8_t*)data_arr, 16);

    // print details
    printf("opcode:  %s\n", old_umi_opcode_to_str(opcode).c_str());
    printf("dstaddr: 0x%016" PRIx64 "\n", dstaddr);
    printf("size:    %u\n", size);
    printf("data:    0x%08x\n", data_arr[0]);
}

int main() {
    // initialize tx connection
    SBTX tx;
    tx.init("rx.q");

    // initialize rx connection
    SBRX rx;
    rx.init("tx.q");

    // packet structure used for sending/receiving
    sb_packet p;

    // write 0xBEEFCAFE to address 0x12
    uint32_t val = 0xBEEFCAFE;
    old_umi_pack((uint32_t*)p.data, OLD_UMI_WRITE_POSTED, 2, 0, 0x12, 0, (uint8_t*)(&val), 4);
    tx.send_blocking(p);
    printf("TX packet: %s\n", old_umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);
    printf("\n");

    // send request to read address 0x12 into address 0x34
    old_umi_pack((uint32_t*)p.data, OLD_UMI_READ_REQUEST, 2, 0, 0x12, 0x34, NULL, 0);
    tx.send_blocking(p);
    printf("TX packet: %s\n", old_umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);
    printf("\n");

    // receive read response
    rx.recv_blocking(p);
    printf("RX packet: %s\n", old_umi_packet_to_str((uint32_t*)p.data).c_str());
    print_packet_details((uint32_t*)p.data);

    return 0;
}
