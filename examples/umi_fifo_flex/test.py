#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from argparse import ArgumentParser
from switchboard import SbDut, UmiTxRx, umi_loopback


def main(n=3, fast=False, tool='verilator'):
    # build simulator
    dut = build_testbench(fast=fast, tool=tool)

    # create queues
    umi = UmiTxRx("to_rtl.q", "from_rtl.q", fresh=True)

    # launch the simulation
    dut.simulate()

    # randomly write data
    umi_loopback(umi, n)


def build_testbench(fast=False, tool='verilator'):
    dut = SbDut(tool=tool, default_main=True)

    EX_DIR = Path('..').resolve()

    dut.input('testbench.sv')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'ramlib' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'stdlib' / 'rtl')

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast, tool=args.tool)
