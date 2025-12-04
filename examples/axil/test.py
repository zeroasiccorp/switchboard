#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import random
import numpy as np

from siliconcompiler import Design

from switchboard import SbDut
from switchboard.verilog.sim.switchboard_sim import SwitchboardSim


def main():
    # build the simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate()

    # run the test: write to random addresses and read back in a random order

    axil = dut.intfs['s_axil']

    addr_bytes = (axil.addr_width + 7) // 8

    model = np.zeros((1 << axil.addr_width,), dtype=np.uint8)

    success = True

    for _ in range(dut.args.n):
        addr = random.randint(0, (1 << axil.addr_width) - 1)
        size = random.randint(1, min(dut.args.max_bytes, (1 << axil.addr_width) - addr))

        if random.random() < 0.5:
            #########
            # write #
            #########

            data = np.random.randint(0, 255, size=size, dtype=np.uint8)

            # perform the write
            axil.write(addr, data)
            print(f'Wrote addr=0x{addr:0{addr_bytes * 2}x} data={data}')

            # update local memory model
            model[addr:addr + size] = data
        else:
            ########
            # read #
            ########

            # perform the read
            data = axil.read(addr, size)
            print(f'Read addr=0x{addr:0{addr_bytes * 2}x} data={data}')

            # check against the model
            if not np.array_equal(data, model[addr:addr + size]):
                print('MISMATCH')
                success = False

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


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


def build_testbench():
    dw = 32
    aw = 13

    parameters = dict(
        DATA_WIDTH=dw,
        ADDR_WIDTH=aw
    )

    interfaces = {
        's_axil': dict(type='axil', dw=dw, aw=aw, direction='subordinate')
    }

    resets = [dict(name='rst', delay=8)]

    extra_args = {
        '-n': dict(type=int, default=10000, help='Number of'
        ' words to write as part of the test.'),
        '--max-bytes': dict(type=int, default=10, help='Maximum'
        ' number of bytes in any single read/write.')
    }

    dut = SbDut(
        design=AxilRam(),
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
