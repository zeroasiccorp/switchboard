#!/usr/bin/env python3

# Copyright (C) 2025 Zero ASIC
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from switchboard import SbDut, AxiLiteTxRx


def main():
    # build the simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate(
        plusargs=[
            ('valid_mode', dut.args.vldmode),
            ('ready_mode', dut.args.rdymode)
        ]
    )

    # Switchboard queue initialization
    axil = AxiLiteTxRx('sb_axil_m',
                      data_width=256,
                      addr_width=8,
                      fresh=True)

    np.set_printoptions(formatter={'int': hex})

    axil.write(0, np.uint8(0xef))
    read_data = axil.read(0, 4)
    print(f'Read addr=0 data={read_data}')

    axil.write(0, np.uint16(0xbeef))
    read_data = axil.read(0, 4)
    print(f'Read addr=0 data={read_data}')

    axil.write(0, np.uint32(0xdeadbeef))
    read_data = axil.read(0, 4)
    print(f'Read addr=0 data={read_data}')

    axil.write(200, np.uint32(0xa0a0a0a0))
    read_data = axil.read(200, 4)
    print(f'Read addr=200 data={read_data}')

    read_data = axil.read(0, 4)
    print(f'Read addr=0 data={read_data}')


def build_testbench(fast=False):

    extra_args = {
        '--vldmode': dict(type=int, default=1, help='Valid mode'),
        '--rdymode': dict(type=int, default=1, help='Ready mode'),
    }

    dut = SbDut('testbench', cmdline=True, extra_args=extra_args,
                trace=False, trace_type='fst', default_main=True)

    dut.register_source(
        'verilog-axi',
        'git+https://github.com/alexforencich/verilog-axi.git',
        '38915fb'
    )

    # Set up inputs
    dut.input('testbench.sv')
    dut.input('rtl/axil_ram.v', package='verilog-axi')

    # Verilator configuration
    dut.add('tool', 'verilator', 'task', 'compile', 'warningoff',
            ['WIDTHTRUNC', 'TIMESCALEMOD'])

    dut.build()

    return dut


if __name__ == '__main__':
    main()
