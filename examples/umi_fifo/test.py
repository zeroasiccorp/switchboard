#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, random_umi_packet, SbDut


def main(n=3, fast=False):
    # build the simulator
    dut = build_testbench(fast=fast)

    # create queues
    umi = UmiTxRx('to_rtl.q', 'from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

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
    dut = SbDut(default_main=True)

    EX_DIR = Path('..').resolve()

    dut.input('testbench.sv')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'ramlib' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'stdlib' / 'rtl')

    dut.build(fast=fast)

    return dut


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast)
