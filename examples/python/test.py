#!/usr/bin/env python3

# Simple example illustrating the Switchboard Python binding

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import numpy as np
from pathlib import Path
from switchboard import PySbPacket, SbDut

THIS_DIR = Path(__file__).resolve().parent
COMMON_DIR = THIS_DIR.parent / 'common'


def main():
    # build the simulator

    interfaces = [
        dict(name='in', type='sb', direction='input'),
        dict(name='out', type='sb', direction='output')
    ]

    dut = SbDut('sb_loopback', autowrap=True, cmdline=True, interfaces=interfaces)
    dut.input(COMMON_DIR / 'verilog' / 'sb_loopback.v')
    dut.build()

    # start chip simulation
    dut.simulate()

    # accesss queues
    tx = dut.get_interface('in')
    rx = dut.get_interface('out')

    # form packet to be sent into the simulation.  note that the arguments
    # to the constructor are all optional, and can all be specified later
    txp = PySbPacket(
        destination=123456789,
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

    success = np.array_equal(rxp.data, txp.data + 1)

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == '__main__':
    main()
