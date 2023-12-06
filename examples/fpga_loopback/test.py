#!/usr/bin/env python3

# Example showing how to interact with a simulation of switchboard's FPGA infrastructure

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import PySbPacket, PySbTx, PySbRx, SbDut


def main(fast=False):
    # build the simulator
    dut = build_testbench(fast=fast)

    # create queues
    tx = PySbTx('to_rtl.q', fresh=True)
    rx = PySbRx('from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

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

    # check received data

    success = np.array_equal(rxp.data, txp.data + 1)

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


def build_testbench(fast=False):
    tool = 'verilator'
    dut = SbDut(tool=tool, default_main=False, fpga=True)

    # Verilog top level

    dut.input('testbench.sv')

    # C++ testbench

    dut.input('testbench.cc')

    # SystemC configuration

    dut.set('tool', tool, 'task', 'compile', 'var', 'mode', 'systemc')
    dut.set('tool', tool, 'task', 'compile', 'threads', 1)
    dut.set('tool', tool, 'task', 'compile', 'var', 'pins_bv', '2')

    # libsystemctlm-soc configuration

    LIBSYSTEMCTLM_SOC = Path('../deps/libsystemctlm-soc').resolve()

    dut.add('tool', tool, 'task', 'compile', 'dir', 'cincludes', LIBSYSTEMCTLM_SOC)
    dut.add('tool', tool, 'task', 'compile', 'dir', 'cincludes', LIBSYSTEMCTLM_SOC / 'tests')
    dut.input(LIBSYSTEMCTLM_SOC / 'trace' / 'trace.cc')

    # build the simulator

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(fast=args.fast)
