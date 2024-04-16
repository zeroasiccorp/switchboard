#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import SbDut, UmiTxRx, umi_loopback
import umi


def main():
    # build simulator
    dut = build_testbench()

    # create queues
    umi = UmiTxRx("to_rtl.q", "from_rtl.q", fresh=True)

    # launch the simulation
    dut.simulate()

    # randomly write data
    umi_loopback(umi, dut.args.n)


def build_testbench():
    extra_args = {
        '-n': dict(type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    }

    dut = SbDut(cmdline=True, default_main=True, extra_args=extra_args)

    dut.input('testbench.sv')

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.build()

    return dut


if __name__ == '__main__':
    main()
