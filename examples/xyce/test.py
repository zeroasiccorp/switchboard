#!/usr/bin/env python3

# Example illustrating mixed-signal simulation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import ArgumentParser
from switchboard import SbDut


def main(fast=False, period=10e-9, tool='verilator'):
    # build the simulator
    dut = SbDut(tool=tool, default_main=True, xyce=True)

    dut.input('testbench.sv')

    dut.ams(
        'rc.cir',
        inputs=[('in', 0.0, 1.0)],
        outputs=[('out', 0.2, 0.8)]
    )

    dut.build(fast=fast)

    # start chip simulation
    chip = dut.simulate(period=period)

    chip.wait()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    parser.add_argument('--period', type=float, default=10e-9,
        help='Period of the oversampling clock')
    args = parser.parse_args()

    main(fast=args.fast, period=args.period, tool=args.tool)
