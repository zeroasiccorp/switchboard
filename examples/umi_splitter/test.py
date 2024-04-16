#!/usr/bin/env python3

# Example illustrating how to interact with the umi_splitter module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import UmiTxRx, random_umi_packet, SbDut
import umi


def main():
    # build the simulator
    dut = build_testbench()

    # get additional command-line arguments
    args = get_additional_args(dut.get_parser())

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

    while (n_sent < args.n) or (n_recv < args.n):
        # try to send a random packet
        if n_sent < args.n:
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
        if n_recv < args.n:
            for i, txq in enumerate([tx_rep, tx_req]):
                rxp = umi_out[i].recv(blocking=False)
                if rxp is not None:
                    print(f'* OUT #{i} *')
                    print(str(rxp))

                    assert txq[0] == rxp
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
