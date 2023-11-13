#!/usr/bin/env python3

# Simple example illustrating the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
import numpy as np
from argparse import ArgumentParser
from switchboard import PySbPacket, PySbTx, PySbRx, SbDut


def main(fast=False):
    # build the simulator
    dut = SbDut(default_main=True)
    dut.input('testbench.sv')
    dut.build(fast=fast)

    # create queues
    tx = PySbTx('client2rtl.q', fresh=True)
    rx = PySbRx('rtl2client.q', fresh=True)

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
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(fast=args.fast)
