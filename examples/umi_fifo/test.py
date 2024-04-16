#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import UmiTxRx, random_umi_packet, SbDut
import umi


def main():
    # build the simulator
    dut = build_testbench()

    # get additional command-line arguments
    args = get_additional_args(dut.get_parser())

    # create queues
    umi = UmiTxRx('to_rtl.q', 'from_rtl.q', fresh=True)

    # launch the simulation
    dut.simulate()

    n_sent = 0
    n_recv = 0
    txq = []

    while (n_sent < args.n) or (n_recv < args.n):
        if n_sent < args.n:
            txp = random_umi_packet()
            if umi.send(txp, blocking=False):
                print('* TX *')
                print(str(txp))
                txq.append(txp)
                n_sent += 1

        if n_recv < args.n:
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                print('* RX *')
                print(str(rxp))
                if rxp != txq[0]:
                    raise Exception('Mismatch!')
                else:
                    txq.pop(0)
                    n_recv += 1


def build_testbench():
    dut = SbDut(cmdline=True, default_main=True)

    dut.input('testbench.sv')

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.build()

    return dut


def get_additional_args(parser):
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')

    return parser.parse_args()


if __name__ == '__main__':
    main()
