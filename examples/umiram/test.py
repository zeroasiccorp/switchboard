#!/usr/bin/env python3

# Example illustrating how to interact with a simple model of UMI memory (umiram)
# Both C++ and Python-based interactions are shown, however Switchboard can be
# used entirely from Python (and we generally recommend doing this.)

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from pathlib import Path
from switchboard import SbDut, UmiTxRx, binary_run
import umi

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


def build_testbench():
    extra_args = {
        '--mode': dict(default='python', choices=['python', 'cpp'],
        help='Programming language used for the test stimulus.')
    }

    dut = SbDut('testbench', cmdline=True, trace_type='fst', extra_args=extra_args)

    dut.input('testbench.sv')
    dut.input(THIS_DIR.parent / 'common' / 'verilog' / 'umiram.sv')

    dut.use(umi)
    dut.add('option', 'library', 'umi')

    dut.build()

    return dut


def main():
    # build the simulator
    dut = build_testbench()

    # create queues
    umi = UmiTxRx('to_rtl.q', 'from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

    if dut.args.mode == 'python':
        python_intf(umi)
    elif dut.args.mode == 'cpp':
        binary_run(THIS_DIR / 'client').wait()
    else:
        raise ValueError(f'Invalid mode: {dut.args.mode}')


if __name__ == '__main__':
    main()
