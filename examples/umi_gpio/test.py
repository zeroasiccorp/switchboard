#!/usr/bin/env python3

# Example illustrating how to interact with the umi_endpoint module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import random
from switchboard import UmiTxRx, SbDut
import umi


def main():
    # build the simulator
    dut = build_testbench()

    # create queues
    umi = UmiTxRx("to_rtl.q", "from_rtl.q", fresh=True)

    # launch the simulation
    dut.simulate()

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

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


def build_testbench():
    dut = SbDut(cmdline=True, default_main=True)

    dut.input('testbench.sv')

    dut.use(umi)
    dut.add('option', 'library', 'umi')

    dut.build()

    return dut


if __name__ == '__main__':
    main()
