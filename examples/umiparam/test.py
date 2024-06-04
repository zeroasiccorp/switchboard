#!/usr/bin/env python3

# Example showing how to set the value of module inputs at runtime without recompilation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import umi
import numpy as np

from switchboard import SbDut

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    dut = build_testbench()

    dut.simulate(plusargs=[('value', 42)])

    value = dut.intfs['udev'].read(0, np.uint32)
    print(f'Read: {value}')

    assert value == 42


def build_testbench():
    dw = 32
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw
    )

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input', txrx='udev'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output', txrx='udev'),
        'value': dict(type='init', width=32, default=77)
    }

    resets = ['nreset']

    dut = SbDut('umiparam', cmdline=True, autowrap=True, parameters=parameters,
        interfaces=interfaces, resets=resets)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.input('../common/verilog/umiparam.sv')

    dut.build()

    return dut


if __name__ == '__main__':
    main()
