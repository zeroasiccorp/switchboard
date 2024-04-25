#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path

from switchboard import SbDut, binary_run

THIS_DIR = Path(__file__).resolve().parent
COMMON_DIR = THIS_DIR.parent / 'common'


def main():
    # build the simulator

    interfaces = [
        dict(name='in', type='sb', direction='input'),
        dict(name='out', type='sb', direction='output')
    ]

    dut = SbDut('sb_loopback', autowrap=True, cmdline=True, interfaces=interfaces)
    dut.input(COMMON_DIR / 'verilog' / 'sb_loopback.v')
    dut.build()

    # start chip and client
    dut.simulate()
    client = binary_run(THIS_DIR / 'client')

    # wait for client and chip to complete
    retcode = client.wait()
    assert retcode == 0


if __name__ == '__main__':
    main()
