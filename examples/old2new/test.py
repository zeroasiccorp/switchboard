#!/usr/bin/env python3

# Example illustrating how to interact with a simple model of UMI memory (umiram)
# Both C++ and Python-based interactions are shown, however Switchboard can be
# used entirely from Python (and we generally recommend doing this.)

# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import SbDut, UmiTxRx, delete_queue, verilator_run

THIS_DIR = Path(__file__).resolve().parent


def main(client2rtl="client2rtl.q", rtl2client="rtl2client.q", fast=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(client2rtl, rtl2client, old=True)

    # write 0xbeefcafe to address 0x12

    wr_addr = 0x12
    wr_data = np.uint32(0xbeefcafe)
    umi.write(wr_addr, wr_data)
    print(f"Wrote to 0x{wr_addr:02x}: 0x{wr_data:08x}")

    # read data from address 0x12

    rd_addr = wr_addr
    rd_data = umi.read(rd_addr, np.uint32)
    print(f"Read from 0x{rd_addr:02x}: 0x{rd_data:08x}")
    assert rd_data == 0xbeefcafe


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
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(fast=args.fast)
