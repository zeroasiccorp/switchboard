#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import SbDut, SbNetwork, umi_loopback
import umi

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # create network

    net = SbNetwork()

    # create the building blocks

    umi_fifo = make_umi_fifo()

    # connect them together

    umi_fifo_0 = net.instantiate(umi_fifo)
    umi_fifo_1 = net.instantiate(umi_fifo)

    net.connect(umi_fifo_0.umi_out, umi_fifo_1.umi_in)

    net.external(umi_fifo_0.umi_in, txrx='umi')
    net.external(umi_fifo_1.umi_out, txrx='umi')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # randomly write data
    umi = net.intfs['umi']
    umi_loopback(umi, 10)


def make_umi_fifo():
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
        'umi_in': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'umi_out': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output')
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

    dut = SbDut('umi_fifo', autowrap=True, extra_args=extra_args, parameters=parameters,
        interfaces=interfaces, clocks=clocks, resets=resets, tieoffs=tieoffs)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    return dut


if __name__ == '__main__':
    main()
