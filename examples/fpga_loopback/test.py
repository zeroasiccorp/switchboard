#!/usr/bin/env python3

# Example showing how to interact with a simulation of switchboard's FPGA infrastructure

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import numpy as np
from argparse import ArgumentParser
from switchboard import PySbPacket, PySbTx, PySbRx, SbDut


def main(n=10, fast=False):
    # build the simulator
    dut = build_testbench(fast=fast)

    # create queues
    tx = PySbTx('to_rtl.q', fresh=True)
    rx = PySbRx('from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

    for _ in range(n):
        # send a packet with random data
        destination = np.random.randint(low=0, high=1 << 32, dtype=np.uint32)
        txdata = np.random.randint(low=0, high=1 << 8, size=(32,), dtype=np.uint8)
        tx.send(PySbPacket(destination=destination, flags=1, data=txdata))

        print(f'Sent: {txdata}')

        # receive the response
        rxdata = rx.recv().data[:32]

        print(f'Received: {rxdata}')

        # check the response
        if not np.array_equal(rxdata, txdata + 1):
            print("FAIL")
            sys.exit(1)

    print("PASS")
    sys.exit(0)


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
    dut.register_source(
        'libsystemctlm-soc',
        'git+https://github.com/Xilinx/libsystemctlm-soc.git',
        '670d73c'
    )

    dut.add('tool', tool, 'task', 'compile', 'dir', 'cincludes', '.',
            package='libsystemctlm-soc')
    dut.add('tool', tool, 'task', 'compile', 'dir', 'cincludes', 'tests',
            package='libsystemctlm-soc')
    dut.input('trace/trace.cc', package='libsystemctlm-soc')

    # build the simulator

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=10, help='Number of'
        ' packets to send during this test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast)
