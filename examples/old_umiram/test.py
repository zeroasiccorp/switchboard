#!/usr/bin/env python3

# Example illustrating how UMI packets are handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, delete_queue, verilator_run, binary_run, SbDut, old2new_run

THIS_DIR = Path(__file__).resolve().parent


def main(mode='python', fast=False, old2new=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # clean up old queues if present

    if old2new:
        from_client = 'from_client.q'
        to_client = 'to_client.q'
        from_rtl = 'from_rtl.q'
        to_rtl = 'to_rtl.q'
        queues = [from_client, to_client, from_rtl, to_rtl]
    else:
        from_client = 'to_rtl.q'
        to_client = 'from_rtl.q'
        queues = [from_client, to_client]

    for q in queues:
        delete_queue(q)

    # start simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    if old2new:
        old2new_run(
            old_tx=to_rtl,
            old_rx=from_rtl,
            new_req_rx=from_client,
            new_resp_tx=to_client
        )

    if mode == 'python':
        python_intf(from_client=from_client, to_client=to_client, old=(not old2new))
    elif mode == 'cpp':
        client = binary_run(THIS_DIR / 'client')
        client.wait()
    else:
        raise ValueError(f'Invalid mode: {mode}')


def python_intf(from_client, to_client, old=True):
    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(from_client, to_client, old=old)

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
    umi.write(0x50, wrbuf, max_bytes=16)

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
    rdbuf = umi.read(0x50, 64, max_bytes=16)
    print("Read: {" + ", ".join([f"0x{elem:02x}" for elem in rdbuf]) + "}")
    assert (rdbuf == np.arange(64, dtype=np.uint8)).all()


def build_testbench(fast=False):
    dut = SbDut('testbench')

    EX_DIR = Path('..')

    # Set up inputs
    dut.input('testbench.sv')
    dut.input(EX_DIR / 'common' / 'old-verilog' / 'umiram.sv')
    dut.input(EX_DIR / 'common' / 'verilator' / 'testbench.cc')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'old-umi' / 'umi' / 'rtl')

    # Verilator configuration
    vlt_config = EX_DIR / 'common' / 'verilator' / 'config.vlt'
    dut.set('tool', 'verilator', 'task', 'compile', 'file', 'config', vlt_config)

    # Settings
    dut.set('option', 'trace', True)  # enable VCD (TODO: FST option)

    result = None

    if fast:
        result = dut.find_result('vexe', step='compile')

    if result is None:
        dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mode', default='python')
    parser.add_argument('--old2new', action='store_true')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(mode=args.mode, fast=args.fast, old2new=args.old2new)
