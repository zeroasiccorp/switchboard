#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module
# Copyright (C) 2023 Zero ASIC

from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, random_umi_packet, verilator_run, SbDut


def main(n=3, fast=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # create queues
    umi = UmiTxRx('client2rtl.q', 'rtl2client.q', fresh=True)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    n_sent = 0
    n_recv = 0
    txq = []

    while (n_sent < n) or (n_recv < n):
        if n_sent < n:
            txp = random_umi_packet()
            if umi.send(txp, blocking=False):
                print('* TX *')
                print(str(txp))
                txq.append(txp)
                n_sent += 1

        if n_recv < n:
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                print('* RX *')
                print(str(rxp))
                if rxp != txq[0]:
                    raise Exception('Mismatch!')
                else:
                    txq.pop(0)
                    n_recv += 1


def build_testbench(fast=False):
    dut = SbDut('testbench', default_main=True)

    EX_DIR = Path('..').resolve()

    # Set up inputs
    dut.input('testbench.sv')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'ramlib' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'stdlib' / 'rtl')

    # Settings
    dut.set('option', 'trace', True)  # enable VCD

    result = None

    if fast:
        result = dut.find_result('vexe', step='compile')

    if result is None:
        dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast)
