// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

#include "switchboard.hpp"
#include "umilib.h"
#include "umilib.hpp"
#include "umisb.hpp"

int main() {
    // initialize tx connection
    SBTX tx;
    tx.init("to_rtl.q");

    // initialize rx connection
    SBRX rx;
    rx.init("from_rtl.q");

    // packet structure used for sending/receiving
    sb_packet p;

    // write 0xBEEFCAFE to address 0x10
    {
        UmiTransaction x;
        uint32_t value = 0xBEEFCAFE;
        x.allocate(2, 0);
        memcpy(x.data, &value, sizeof(value));
        x.cmd = umi_pack(UMI_REQ_POSTED, 0, 2, 0, 1, 1);
        x.dstaddr = 0x10;
        umisb_send<UmiTransaction>(x, tx, true);
        printf("*** TX ***\n");
        std::cout << umi_transaction_as_str<UmiTransaction>(x) << std::endl;
    }

    // send request to read address 0x10 into address 0x20
    {
        UmiTransaction y;
        y.cmd = umi_pack(UMI_REQ_READ, 0, 2, 0, 1, 1);
        y.dstaddr = 0x10;
        y.srcaddr = 0x20;
        umisb_send<UmiTransaction>(y, tx, true);
        tx.send_blocking(p);
        printf("*** TX ***\n");
        std::cout << umi_transaction_as_str<UmiTransaction>(y) << std::endl;
    }

    // receive read response
    {
        UmiTransaction z;
        umisb_recv<UmiTransaction>(z, rx, true);
        printf("*** RX ***\n");
        std::cout << umi_transaction_as_str<UmiTransaction>(z) << std::endl;
    }

    return 0;
}
