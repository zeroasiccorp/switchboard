#!/usr/bin/env python3

# Example illustrating mixed-signal simulation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import ArgumentParser
from switchboard import SbDut


def main(fast=False, period=10e-9, tool='verilator'):
    # create the simulator object

    dut = SbDut(tool=tool, default_main=True)

    dut.input('testbench.sv')

    # specify the analog subcircuit

    vdd = 1.0

    params = dict(
        vol=0,
        voh=vdd,
        vil=0.2 * vdd,
        vih=0.8 * vdd
    )

    dut.input_analog(
        'mycircuit.cir',
        pins=[
            dict(name='a', type='input', **params),
            dict(name='b[1:0]', type='input', **params),
            dict(name='y', type='output', **params),
            dict(name='z[1:0]', type='output', **params),
            dict(name='vss', type='constant', value=0)
        ]
    )

    # build the simulator

    dut.build(fast=fast)

    # start the simulator

    chip = dut.simulate(period=period)

    # wait for the simulation to complete

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
