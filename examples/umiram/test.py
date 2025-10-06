#!/usr/bin/env python3

# Example illustrating how to interact with a simple model of UMI memory (umiram)
# Both C++ and Python-based interactions are shown, however Switchboard can be
# used entirely from Python (and we generally recommend doing this.)

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from pathlib import Path
from switchboard import SbDut, UmiTxRx, binary_run
from umi.sumi import Fifo, RAM

from siliconcompiler import Design


THIS_DIR = Path(__file__).resolve().parent


def python_intf(umi):
    print("### WRITES ###")

    # 1 byte
    wrbuf = np.array([0x0D, 0xF0, 0xAD, 0xBA], np.uint8)
    for i in range(4):
        umi.write(0x10 + i, wrbuf[i])

    # 2 bytes
    wrbuf = np.array([0xCAFE, 0xB0BA], np.uint16)
    umi.write(0x20, wrbuf)

    # 4 bytes
    umi.write(0x30, np.uint32(0xDEADBEEF))

    # 8 bytes
    umi.write(0x40, np.uint64(0xBAADD00DCAFEFACE))

    # 64 bytes
    wrbuf = np.arange(64, dtype=np.uint8)
    umi.write(0x80, wrbuf)

    print("### READS ###")

    # 1 byte
    rdbuf = umi.read(0x10, 4, np.uint8)
    val32 = rdbuf.view(np.uint32)[0]
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xBAADF00D

    # 2 bytes
    rdbuf = umi.read(0x20, 2, np.uint16)
    val32 = rdbuf.view(np.uint32)[0]
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xB0BACAFE

    # 4 bytes
    val32 = umi.read(0x30, np.uint32)
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xDEADBEEF

    # 8 bytes
    val64 = umi.read(0x40, np.uint64)
    print(f"Read: 0x{val64:016x}")
    assert val64 == 0xBAADD00DCAFEFACE

    # 64 bytes
    rdbuf = umi.read(0x80, 64)
    print("Read: {" + ", ".join([f"0x{elem:02x}" for elem in rdbuf]) + "}")
    assert (rdbuf == np.arange(64, dtype=np.uint8)).all()

    print("### ATOMICS ###")

    umi.write(0xC0, np.uint32(0x12))
    val1 = umi.atomic(0xC0, np.uint32(0x34), 'add')
    val2 = umi.read(0xC0, np.uint32)
    print(f'val1: {val1}, val2: {val2}')
    assert val1 == 0x12
    assert val2 == (0x12 + 0x34)

    umi.write(0xD0, np.uint64(0xAB))
    val1 = umi.atomic(0xD0, np.uint64(0xCD), 'swap')
    val2 = umi.read(0xD0, np.uint64)
    print(f'val1: {val1}, val2: {val2}')
    assert val1 == 0xAB
    assert val2 == 0xCD


class UmiRam(Design):

    def __init__(self):
        super().__init__("testbench")

        from switchboard import sb_path

        from switchboard.verilog.common.common import Common
        from switchboard.verilog.sim.sim import Sim as SB_SIM

        dr_path = sb_path() / ".." / "examples" / "umiram"

        self.set_dataroot('umiram', dr_path)

        files = [
            "testbench.sv",
            "../common/verilog/umiram.sv"
        ]

        deps = [Common(), SB_SIM(), Fifo(), RAM()]

        with self.active_fileset('rtl'):
            self.set_topmodule("testbench")
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)


def build_testbench():
    extra_args = {
        '--mode': dict(default='python', choices=['python', 'cpp'],
        help='Programming language used for the test stimulus.')
    }

    dut = SbDut(UmiRam())
    dut.option.set_nodashboard(True)

    print(f"dut.build() output = {dut.build()}")

    return dut


def main():
    # build the simulator
    dut = build_testbench()

    # create queues
    umi = UmiTxRx('to_rtl.q', 'from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

    #if dut.args.mode == 'python':
    #python_intf(umi)
    #elif dut.args.mode == 'cpp':
    binary_run(THIS_DIR / 'client').wait()
    #else:
    #    raise ValueError(f'Invalid mode: {dut.args.mode}')


if __name__ == '__main__':
    main()
