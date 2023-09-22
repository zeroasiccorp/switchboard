#!/usr/bin/env python3

# Example illustrating how to interact with the umi_endpoint module
# Copyright (C) 2023 Zero ASIC

import random
from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, delete_queue, verilator_run, SbDut


def main(client2rtl="client2rtl.q", rtl2client="rtl2client.q", fast=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(client2rtl, rtl2client)
    gpio = umi.gpio(owidth=128, iwidth=384, init=0xcafed00d)

    print(f'Initial value: 0x{gpio.o[:]:x}')
    assert gpio.o[:] == 0xcafed00d

    # drive outputs

    gpio.o[7:0] = 22
    print(f'gpio.o[7:0] = {gpio.o[7:0]}')
    assert gpio.o[7:0] == 22

    gpio.o[15:8] = 77
    print(f'gpio.o[15:8] = {gpio.o[15:8]}')
    assert gpio.o[15:8] == 77

    # read first input

    a = gpio.i[7:0]
    print(f'Got gpio.i[7:0] = {a}')
    assert a == 34

    # read second input

    b = gpio.i[15:8]
    print(f'Got gpio.i[15:8] = {b}')
    assert b == 43

    # show that long values work

    stimulus = random.randint(0, (1 << 128) - 1)

    gpio.o[:] = stimulus
    print(f'Wrote gpio.o[:] = 0x{gpio.o[:]:032x}')

    c = gpio.i[255:128]
    print(f'Read gpio.i[255:128] = 0x{c:032x}')
    assert c == stimulus

    d = gpio.i[383:256]
    print(f'Read gpio.i[383:256] = 0x{d:032x}')
    assert d == (~stimulus) & ((1 << 128) - 1)

    print('PASS!')


def build_testbench(fast=False):
    dut = SbDut('testbench')

    EX_DIR = Path('..').resolve()

    # Set up inputs
    dut.input('testbench.sv')
    dut.input(EX_DIR / 'common' / 'verilator' / 'testbench.cc')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')

    # Verilator configuration
    vlt_config = EX_DIR / 'common' / 'verilator' / 'config.vlt'
    dut.set('tool', 'verilator', 'task', 'compile', 'file', 'config', vlt_config)

    # Settings
    dut.set('option', 'trace', True)  # enable VCD (TODO: FST option)

    result = None

    if fast:
        result = dut.find_result('vexe', step='compile')

    if result is None:
        dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(fast=args.fast)
