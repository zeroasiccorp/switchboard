#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import switchboard, UmiTxRx, delete_queue, verilator_run, binary_run
from siliconcompiler import Chip
from siliconcompiler.tools.verilator import compile

THIS_DIR = Path(__file__).resolve().parent


def build_testbench():
    chip = Chip('testbench')

    SB_DIR = switchboard.path()
    EX_DIR = Path('..')

    # Set up inputs
    chip.input('testbench.sv')
    chip.input(EX_DIR / 'common' / 'verilog' / 'umiram.sv')
    chip.input(EX_DIR / 'common' / 'verilator' / 'testbench.cc')
    chip.input(SB_DIR / 'dpi' / 'switchboard_dpi.cc')

    chip.add('option', 'ydir', SB_DIR / 'verilog' / 'sim')
    chip.add('option', 'ydir', EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
    chip.add('option', 'idir', EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')

    # Verilator configuration
    c_flags = ['-Wno-unknown-warning-option']
    c_includes = [SB_DIR / 'cpp']
    ld_flags = ['-pthread']
    vlt_config = EX_DIR / 'common' / 'verilator' / 'config.vlt'

    chip.set('tool', 'verilator', 'task', 'compile', 'var', 'cflags', c_flags)
    chip.set('tool', 'verilator', 'task', 'compile', 'dir', 'cincludes', c_includes)
    chip.set('tool', 'verilator', 'task', 'compile', 'var', 'ldflags', ld_flags)
    chip.set('tool', 'verilator', 'task', 'compile', 'file', 'config', vlt_config)

    # Generic settings
    chip.set('option', 'trace', True)  # enable VCD (TODO: FST option)
    chip.set('option', 'mode', 'sim')

    # Set up flow that runs Verilator compile
    # TODO: this will be built into SC
    chip.set('option', 'flow', 'simflow')
    chip.node('simflow', 'compile', compile)

    # Run and entire result
    chip.run()

    return chip.find_result('vexe', step='compile')


def main(mode='python', client2rtl="client2rtl.q", rtl2client="rtl2client.q"):
    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    verilator_bin = build_testbench()

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    if mode == 'python':
        python_intf(client2rtl=client2rtl, rtl2client=rtl2client)
    elif mode == 'cpp':
        client = binary_run(THIS_DIR / 'client')
        client.wait()
    else:
        raise ValueError(f'Invalid mode: {mode}')


def python_intf(client2rtl, rtl2client):
    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(client2rtl, rtl2client)

    print("### WRITES ###")

    # 1 byte
    wrbuf = np.array([0xBAADF00D], np.uint32).view(np.uint8)
    for i in range(4):
        umi.write(0x10 + i, wrbuf[i])

    # 2 bytes
    wrbuf = np.array([0xB0BACAFE], np.uint32).view(np.uint16)
    umi.write(0x20, wrbuf)

    # 4 bytes
    umi.write(0x30, np.uint32(0xDEADBEEF))

    # 8 bytes
    umi.write(0x40, np.uint64(0xBAADD00DCAFEFACE))

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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mode', default='python')
    args = parser.parse_args()

    main(mode=args.mode)
