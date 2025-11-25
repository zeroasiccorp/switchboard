#!/usr/bin/env python3

# Copyright (C) 2025 Zero ASIC
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from siliconcompiler import Design

from switchboard import SbDut, AxiLiteTxRx

from switchboard.verilog.sim.switchboard_sim import SwitchboardSim
from switchboard import sb_path


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


class AxilRam(Design):

    def __init__(self):
        super().__init__("axilram")

        top_module = "axil_ram"

        self.set_dataroot(
            name="verilog-axi",
            path="git+https://github.com/alexforencich/verilog-axi.git",
            tag="38915fb"
        )

        files = [
            "rtl/axil_ram.v"
        ]

        with self.active_fileset('rtl'):
            self.set_topmodule(top_module)
            self.add_depfileset(SwitchboardSim())
            for item in files:
                self.add_file(item)

        with self.active_fileset('verilator'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")

        with self.active_fileset('icarus'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")


class TB(Design):

    def __init__(self):
        super().__init__("TB")

        top_module = "testbench"

        dr_path = sb_path() / ".." / "examples" / "axil_ram"

        self.set_dataroot('axil_ram', dr_path)

        files = [
            "testbench.sv"
        ]

        deps = [
            AxilRam()
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
            self.add_depfileset(SwitchboardSim())
            self.add_depfileset(self, "rtl")

        with self.active_fileset('icarus'):
            self.set_topmodule(top_module)
            self.add_depfileset(SwitchboardSim())
            self.add_depfileset(self, "rtl")


def build_testbench(fast=False):

    extra_args = {
        '--vldmode': dict(type=int, default=1, help='Valid mode'),
        '--rdymode': dict(type=int, default=1, help='Ready mode'),
    }

    dut = SbDut(
        design=TB(),
        extra_args=extra_args,
        cmdline=True
    )

    dut.build()

    return dut


if __name__ == '__main__':
    main()
