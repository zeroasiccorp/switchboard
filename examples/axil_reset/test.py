#!/usr/bin/env python3

# Regression test for https://github.com/zeroasiccorp/switchboard/issues/275:
# transactors must not drive transactions into a DUT that is still in reset.

# Copyright (c) 2026 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys

import numpy as np

from siliconcompiler import Design

from switchboard import SbDut
from switchboard.verilog.sim.switchboard_sim import SwitchboardSim


def main():
    # build the simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate()

    axil = dut.intfs['s_axil']

    # the DUT counts every transaction accepted while it was in reset, and
    # returns that count for any read.  drive some traffic first, so that a
    # transactor which ignores reset has something to get wrong.
    for addr in range(0, 4 * dut.args.n, 4):
        axil.write(addr % 256, np.uint32(addr))

    rst_xacts = int(axil.read(0, np.uint32))

    print(f'Transactions accepted during reset: {rst_xacts}')

    if rst_xacts == 0:
        print("PASS!")
        sys.exit(0)
    else:
        print(f'FAIL: {rst_xacts} transaction(s) were driven into the DUT while'
              ' it was still in reset')
        sys.exit(1)


class AxilResetCheck(Design):

    def __init__(self):
        super().__init__("axil_reset_check")

        top_module = "axil_reset_check"

        self.set_dataroot("axil_reset", __file__)

        with self.active_fileset('rtl'):
            self.set_topmodule(top_module)
            self.add_depfileset(SwitchboardSim())
            self.add_file("axil_reset_check.sv")

        with self.active_fileset('verilator'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")

        with self.active_fileset('icarus'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")


def build_testbench():
    dw = 32
    aw = 8

    parameters = dict(
        DATA_WIDTH=dw,
        ADDR_WIDTH=aw
    )

    interfaces = {
        's_axil': dict(type='axil', dw=dw, aw=aw, direction='subordinate')
    }

    # a long reset makes the failure deterministic: without the fix the
    # transactor drives a transaction on essentially the first clock edge
    resets = [dict(name='rst', delay=8)]

    extra_args = {
        '-n': dict(type=int, default=16, help='Number of writes to perform.')
    }

    dut = SbDut(
        design=AxilResetCheck(),
        cmdline=True,
        autowrap=True,
        parameters=parameters,
        interfaces=interfaces,
        resets=resets,
        extra_args=extra_args
    )

    dut.build()

    return dut


if __name__ == '__main__':
    main()
