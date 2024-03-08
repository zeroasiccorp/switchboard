#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import ArgumentParser
from switchboard import SbDut, AxiLiteTxRx


def main(fast=False, tool='verilator'):
    # build the simulator
    dut = build_testbench(fast=fast, tool=tool)

    # create the queues
    axil = AxiLiteTxRx('axil')

    # launch the simulation
    dut.simulate()

    # run the test

    axil.write(addr=12, data=23)
    axil.write(addr=34, data=45)
    axil.write(addr=56, data=67)

    print(axil.read(addr=12))
    print(axil.read(addr=34))
    print(axil.read(addr=56))


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
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    args = parser.parse_args()

    main(fast=args.fast, tool=args.tool)
