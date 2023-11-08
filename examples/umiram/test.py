#!/usr/bin/env python3

# Example illustrating how to interact with a simple model of UMI memory (umiram)
# Both C++ and Python-based interactions are shown, however Switchboard can be
# used entirely from Python (and we generally recommend doing this.)

# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import SbDut, UmiTxRx, binary_run

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


def build_testbench(fast=False):
    dut = SbDut('testbench', default_main=True, trace_type='fst')

    EX_DIR = Path('..').resolve()

    dut.input('testbench.sv')
    dut.input(EX_DIR / 'common' / 'verilog' / 'umiram.sv')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')

    dut.build(fast=fast)

    return dut


def main(mode='python', fast=False):
    # build the simulator
    dut = build_testbench(fast=fast)

    # create queues
    umi = UmiTxRx('to_rtl.q', 'from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

    if mode == 'python':
        python_intf(umi)
    elif mode == 'cpp':
        binary_run(THIS_DIR / 'client').wait()
    else:
        raise ValueError(f'Invalid mode: {mode}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mode', default='python')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(mode=args.mode, fast=args.fast)
