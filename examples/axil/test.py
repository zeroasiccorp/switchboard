#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import random
import numpy as np

from argparse import ArgumentParser
from switchboard import SbDut, AxiLiteTxRx


def main(n=100, fast=False, tool='verilator', max_bytes=10):
    # build the simulator
    dut = build_testbench(fast=fast, tool=tool)

    # create the queues
    axil = AxiLiteTxRx('axil', data_width=32, addr_width=8)

    # launch the simulation
    dut.simulate()

    # run the test: write to random addresses and read back in a random order

    addr_bytes = (axil.addr_width + 7) // 8

    model = np.zeros((1 << axil.addr_width,), dtype=np.uint8)

    success = True

    for _ in range(n):
        addr = random.randint(0, (1 << axil.addr_width) - 1)
        size = random.randint(1, min(max_bytes, (1 << axil.addr_width) - addr))

        if random.random() < 0.5:
            #########
            # write #
            #########

            data = np.random.randint(0, 255, size=size, dtype=np.uint8)

            # perform the write
            axil.write(addr, data)
            print(f'Wrote addr=0x{addr:0{addr_bytes * 2}x} data={data}')

            # update local memory model
            model[addr:addr + size] = data
        else:
            ########
            # read #
            ########

            # perform the read
            data = axil.read(addr, size)
            print(f'Read addr=0x{addr:0{addr_bytes * 2}x} data={data}')

            # check against the model
            if not np.array_equal(data, model[addr:addr + size]):
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

    dut.add('tool', 'verilator', 'task', 'compile', 'warningoff', ['WIDTHTRUNC', 'TIMESCALEMOD'])

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=100, help='Number of'
        ' words to write as part of the test.')
    parser.add_argument('--max-bytes', type=int, default=10, help='Maximum'
        ' number of bytes in any single read/write.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast, tool=args.tool, max_bytes=args.max_bytes)
