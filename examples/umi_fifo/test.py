#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import random_umi_packet, SbDut
from umi import sumi


def main():
    # build the simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate()

    umi = dut.intfs['umi']

    n_sent = 0
    n_recv = 0
    txq = []

    while (n_sent < dut.args.n) or (n_recv < dut.args.n):
        if n_sent < dut.args.n:
            txp = random_umi_packet()
            if umi.send(txp, blocking=False):
                print('* TX *')
                print(str(txp))
                txq.append(txp)
                n_sent += 1

        if n_recv < dut.args.n:
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
    dw = 256
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw
    )

    tieoffs = dict(
        bypass="1'b0",
        chaosmode="1'b0",
        fifo_full=None,
        fifo_empty=None,
        vdd="1'b1",
        vss="1'b0"
    )

    interfaces = {
        'umi_in': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input', txrx='umi'),
        'umi_out': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output', txrx='umi')
    }

    clocks = [
        'umi_in_clk',
        'umi_out_clk'
    ]

    resets = [
        'umi_in_nreset',
        'umi_out_nreset'
    ]

    extra_args = {
        '-n': dict(type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    }

    dut = SbDut('umi_fifo', autowrap=True, cmdline=True, extra_args=extra_args,
        parameters=parameters, interfaces=interfaces, clocks=clocks, resets=resets,
        tieoffs=tieoffs)

    dut.use(sumi)

    dut.build()

    return dut


if __name__ == '__main__':
    main()
