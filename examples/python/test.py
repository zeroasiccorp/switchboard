#!/usr/bin/env python3

# Simple example illustrating the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
import numpy as np
from argparse import ArgumentParser
from switchboard import PySbPacket, PySbTx, PySbRx, verilator_run, SbDut


def main(fast=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # create queues
    tx = PySbTx('client2rtl.q', fresh=True)
    rx = PySbRx('rtl2client.q', fresh=True)

    # start chip simulation
    chip = verilator_run(verilator_bin, plusargs=['trace'])

    # form packet to be sent into the simulation.  note that the arguments
    # to the constructor are all optional, and can all be specified later
    txp = PySbPacket(
        destination=123456789,
        flags=1,
        data=np.array([(i & 0xff) for i in range(32)], dtype=np.uint8)
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

    success = (rxp.data == (txp.data + 1)).all()

    # stop simulation

    tx.send(PySbPacket(data=np.array([0xff for _ in range(32)], dtype=np.uint8)))
    chip.wait()

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


def build_testbench(fast=False):
    dut = SbDut('testbench', default_main=True)

    # Set up inputs
    dut.input('testbench.sv')

    # Settings
    dut.set('option', 'trace', True)  # enable VCD

    result = None

    if fast:
        result = dut.find_result('vexe', step='compile')

    if result is None:
        dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(fast=args.fast)
