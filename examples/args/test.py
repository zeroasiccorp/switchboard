#!/usr/bin/env python3

# Example showing how to pass a custom argument to a simulation binary

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import ArgumentParser, REMAINDER
from switchboard import SbDut


def main(fast=False, tool='verilator', args=None):
    dut = SbDut(tool=tool, default_main=True)
    dut.input('testbench.sv')
    dut.build(fast=fast)
    dut.simulate(args=args).wait()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    parser.add_argument('args', nargs=REMAINDER,
        help='Arguments to pass directly to the simulation.')
    args = parser.parse_args()

    main(fast=args.fast, tool=args.tool, args=args.args)
