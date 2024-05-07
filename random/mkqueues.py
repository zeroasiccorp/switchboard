#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

# Small script that generates sample queues for inspection with a command-line tool

import numpy as np
from switchboard import PySbTx, PySbPacket, UmiTxRx, random_umi_packet


def main():
    #######################################
    # generate native switchboard packets #
    #######################################

    print('*** Native packets ***')
    print()

    tx = PySbTx('sb.q', fresh=True)

    txp = PySbPacket(
        destination=2,
        flags=1,
        data=np.arange(32, dtype=np.uint8)
    )

    for k in range(3):
        print(txp)
        tx.send(txp)

        txp.data += 1
        txp.flags = 1 - txp.flags
        txp.destination = (txp.destination * 10) + (k + 3)

    print()

    ########################
    # generate UMI packets #
    ########################

    print('*** UMI packets ***')
    print()

    tx = UmiTxRx(tx_uri='umi.q', fresh=True)

    for k in range(3):
        txp = random_umi_packet()
        print(txp)
        tx.send(txp)


if __name__ == '__main__':
    main()
