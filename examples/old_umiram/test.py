#!/usr/bin/env python3

# Example illustrating how UMI packets are handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, delete_queue, verilator_run, binary_run, SbDut

THIS_DIR = Path(__file__).resolve().parent


def main(mode='python', rxq='rx.q', txq='tx.q'):
    # build the simulator
    verilator_bin = build_testbench()

    # clean up old queues if present
    for q in [rxq, txq]:
        delete_queue(q)

    # start simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    if mode == 'python':
        python_intf(rxq=rxq, txq=txq)
    elif mode == 'cpp':
        client = binary_run(THIS_DIR / 'client')
        client.wait()
    else:
        raise ValueError(f'Invalid mode: {mode}')


def python_intf(rxq, txq):
    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(rxq, txq, old=True)

    # write 0xbeefcafe to address 0x12

    wr_addr = 0x12
    wr_data = np.uint32(0xbeefcafe)
    umi.write(wr_addr, wr_data)
    print(f"Wrote to 0x{wr_addr:02x}: 0x{wr_data:08x}")

    # read data from address 0x12

    rd_addr = wr_addr
    rd_data = umi.read(rd_addr, np.uint32)
    print(f"Read from 0x{rd_addr:02x}: 0x{rd_data:08x}")

    # declare test as having passed for regression testing purposes

    if rd_data == wr_data:
        print('PASS!')
        sys.exit(0)
    else:
        print('FAIL')
        sys.exit(1)


def build_testbench():
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

    # Build simulator
    dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mode', default='python')
    args = parser.parse_args()

    main(mode=args.mode)
