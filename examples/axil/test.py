#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import random

from argparse import ArgumentParser
from switchboard import SbDut, AxiLiteTxRx


def main(n=3, fast=False, tool='verilator'):
    # build the simulator
    dut = build_testbench(fast=fast, tool=tool)

    # create the queues
    axil = AxiLiteTxRx('axil')

    # launch the simulation
    dut.simulate()

    # run the test: write to random addresses and read back in a random order

    model = {}

    addr_bytes = axil.addr_width // 8
    data_bytes = axil.data_width // 8

    for _ in range(n):
        # generate a random write transaction, observing that memory addresses
        # increment by the number of bytes in a data word.  for example, if
        # addr_width=16 and data_width=32, there are 4 bytes in a data word.
        # hence, addresses 0-3 all refer to the same slot in memory. same for
        # addresses 4-7, 8-11, etc.

        addr = random.randint(0, ((1 << axil.addr_width) // data_bytes) - 1) * data_bytes
        data = random.randint(0, (1 << axil.data_width) - 1)

        # update local memory model
        model[addr] = data

        # perform the write
        axil.write(addr=addr, data=data)
        print(f'Wrote addr=0x{addr:0{addr_bytes * 2}x} data=0x{data:0{data_bytes * 2}x}')

    # shuffle the addresses to read back in a random order

    addresses = list(model.keys())
    random.shuffle(addresses)

    success = True

    for addr in addresses:
        # perform the read
        data = axil.read(addr=addr)
        print(f'Read addr=0x{addr:0{addr_bytes * 2}x} data=0x{data:0{data_bytes * 2}x}')

        # check the result
        if data != model[addr]:
            print('MISMATCH')
            success = False

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


def build_testbench(fast=False, tool='verilator'):
    dut = SbDut(tool=tool, default_main=True)

    dut.register_package_source(
        'verilog-axi',
        'git+https://github.com/alexforencich/verilog-axi.git',
        '38915fb'
    )

    dut.input('rtl/axil_ram.v', package='verilog-axi')
    dut.input('testbench.sv')

    dut.add('tool', 'verilator', 'task', 'compile', 'warningoff', 'WIDTHTRUNC')
    dut.add('tool', 'verilator', 'task', 'compile', 'warningoff', 'TIMESCALEMOD')

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' words to write as part of the test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast, tool=args.tool)
