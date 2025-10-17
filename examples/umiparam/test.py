#!/usr/bin/env python3

# Example showing how to set the value of module inputs at runtime without recompilation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from umi.sumi import Endpoint

from siliconcompiler import Design

from switchboard import SbDut
from switchboard import sb_path
from switchboard.verilog.sim.switchboard_sim import SwitchboardSim

from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent


def main():
    dut = build_testbench()

    dut.simulate(plusargs=[('value', 42)])

    value = dut.intfs['udev'].read(0, np.uint32)
    print(f'Read: {value}')

    assert value == 42


class UmiParam(Design):

    def __init__(self):
        super().__init__("umiparam")

        top_module = "umiparam"

        dr_path = sb_path() / ".." / "examples" / "common"

        self.set_dataroot('sb_ex_common', dr_path)

        files = [
            "verilog/umiparam.sv"
        ]

        deps = [
            Endpoint()
        ]

        with self.active_fileset('rtl'):
            self.set_topmodule(top_module)
            self.add_depfileset(SwitchboardSim())
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)

        with self.active_fileset('verilator'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")

        with self.active_fileset('icarus'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")


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
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input', txrx='udev', reset='nreset'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output', txrx='udev', reset='nreset'),
        'value': dict(type='plusarg', width=32, default=77)
    }

    resets = ['nreset']

    dut = SbDut(
        UmiParam(),
        cmdline=True,
        autowrap=True,
        parameters=parameters,
        interfaces=interfaces,
        resets=resets
    )

    dut.build()

    return dut


if __name__ == '__main__':
    main()
