#!/usr/bin/env python3

# Example illustrating how to interact with the umi_splitter module

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, random_umi_packet, SbDut


def main(n=3, fast=False, tool='verilator'):
    # build the simulator
    dut = build_testbench(fast=fast, tool=tool)

    # create queues
    umi_in = UmiTxRx("in.q", "", fresh=True)
    umi_out = [
        UmiTxRx("", "out0.q", fresh=True),
        UmiTxRx("", "out1.q", fresh=True)
    ]

    # launch the simulation
    dut.simulate()

    # main loop
    tx_rep = []
    tx_req = []
    n_sent = 0
    n_recv = 0

    while (n_sent < n) or (n_recv < n):
        # try to send a random packet
        if n_sent < n:
            txp = random_umi_packet()
            if umi_in.send(txp, blocking=False):
                print('* IN *')
                print(str(txp))

                if (txp.cmd & 1) == 0:
                    # replies have the lsb of cmd set to "0"
                    tx_rep.append(txp)
                else:
                    # requests have the lsb of cmd set to "1"
                    tx_req.append(txp)

                n_sent += 1

        # try to receive from both outputs
        if n_recv < n:
            for i, txq in enumerate([tx_rep, tx_req]):
                rxp = umi_out[i].recv(blocking=False)
                if rxp is not None:
                    print(f'* OUT #{i} *')
                    print(str(rxp))

                    assert txq[0] == rxp
                    txq.pop(0)

                    n_recv += 1


def build_testbench(fast=False, tool='verilator'):
    dut = SbDut(tool=tool, default_main=True)

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
    parser.add_argument('--tool', default='verilator', choices=['icarus', 'verilator'],
        help='Name of the simulator to use.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast, tool=args.tool)
