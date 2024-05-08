#!/usr/bin/env python3

# Simple example illustrating switchboard bridging over TCP.

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import numpy as np
from switchboard import PySbPacket, PySbTx, PySbRx, start_tcp_bridge


def main(txq='tx.q', rxq='rx.q'):
    # create queues
    tx = PySbTx(txq, fresh=True)
    rx = PySbRx(rxq, fresh=True)

    # start TCP bridges
    start_tcp_bridge(inputs=[txq])
    start_tcp_bridge(outputs={0: rxq})

    # form packet to be sent into the simulation.  note that the arguments
    # to the constructor are all optional, and can all be specified later
    txp = PySbPacket(
        destination=0,
        flags=1,
        data=np.arange(32, dtype=np.uint8)
    )

    # send the packet

    tx.send(txp)  # note: blocking by default, can disable with blocking=False
    print("*** TX packet ***")
    print(txp)
    print()

    # receive packet

    rxp = rx.recv()  # note: blocking by default, can disable with blocking=False
    rxp.data = rxp.data[:32]

    print("*** RX packet ***")
    print(rxp)
    print()

    # check that the received data

    success = np.array_equal(rxp.data, txp.data)

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == '__main__':
    main()
