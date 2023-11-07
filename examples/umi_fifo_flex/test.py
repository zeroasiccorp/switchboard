#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module
# Copyright (C) 2023 Zero ASIC

from pathlib import Path
from argparse import ArgumentParser
from switchboard import SbDut, UmiTxRx, verilator_run, umi_loopback


def main(n=3, fast=False):
    # build simulator
    verilator_bin = build_testbench(fast=fast)

    # create queues
    umi = UmiTxRx("client2rtl.q", "rtl2client.q", fresh=True)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # randomly write data
    umi_loopback(umi, n)


def build_testbench(fast=False):
    dut = SbDut('testbench', default_main=True)

    EX_DIR = Path('..').resolve()

    # Set up inputs
    dut.input('testbench.sv')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'ramlib' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'stdlib' / 'rtl')

    # Settings
    dut.set('option', 'trace', True)  # enable VCD

    result = None

    if fast:
        result = dut.find_result('vexe', step='compile')

    if result is None:
        dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast)
