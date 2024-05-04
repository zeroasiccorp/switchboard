#!/usr/bin/env python3

# Simple example illustrating the Switchboard Python binding

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import numpy as np
from switchboard import PySbPacket, PySbTx, PySbRx, SbDut


def main():
    # build the simulator
    dut = SbDut(cmdline=True)
    dut.input('testbench.sv')
    dut.build()

    # create queues
    tx = PySbTx('to_rtl.q', fresh=True)
    rx = PySbRx('from_rtl.q', fresh=True)

    # start chip simulation
    chip = dut.simulate()

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

    # stop simulation

    tx.send(PySbPacket(data=np.array([0xff] * 32, dtype=np.uint8)))
    chip.wait()

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == '__main__':
    main()
