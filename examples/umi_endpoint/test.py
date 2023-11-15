#!/usr/bin/env python3

# Example illustrating how to interact with the umi_endpoint module

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, SbDut


def main(fast=False):
    # build the simulator
    dut = build_testbench(fast=fast)

    # create queues
    umi = UmiTxRx("client2rtl.q", "rtl2client.q", fresh=True)

    # launch the simulation
    dut.simulate()

    print("### MINIMAL EXAMPLE ###")

    umi.write(0x0, np.uint32(0xDEADBEEF))
    rdval = umi.read(0x0, np.uint32)
    print(f"Read: 0x{rdval:08x}")
    assert rdval == 0xDEADBEEF

    print("### WRITES ###")

    # 1 byte
    wrbuf = np.array([0xBAADF00D], np.uint32).view(np.uint8)
    for i in range(4):
        umi.write(0x10 + i, wrbuf[i])

    # 2 bytes
    wrbuf = np.array([0xB0BACAFE], np.uint32).view(np.uint16)
    for i in range(2):
        umi.write(0x20 + 2 * i, wrbuf[i])

    # 4 bytes
    umi.write(0x30, np.uint32(0xDEADBEEF))

    # 8 bytes
    umi.write(0x40, np.uint64(0xBAADD00DCAFEFACE))

    print("### READS ###")

    # 1 byte
    rdbuf = np.empty((4,), dtype=np.uint8)
    for i in range(4):
        rdbuf[i] = umi.read(0x10 + i, np.uint8)
    val32 = rdbuf.view(np.uint32)[0]
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xBAADF00D

    # 2 bytes
    rdbuf = np.empty((2,), dtype=np.uint16)
    for i in range(2):
        rdbuf[i] = umi.read(0x20 + 2 * i, np.uint16)
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


def build_testbench(fast=False):
    dut = SbDut(default_main=True)

    EX_DIR = Path('..').resolve()

    dut.input('testbench.sv')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'stdlib' / 'rtl')

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(fast=args.fast)
