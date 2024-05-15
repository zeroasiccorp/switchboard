#!/usr/bin/env python3

# Example showing how to wire up various modules using SbNetwork

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import umi
from switchboard import SbNetwork, umi_loopback

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # create network

    extra_args = {
        '--packets': dict(type=int, default=1000, help='Number of'
        ' transactions to send into the FIFO during the test.'),
        '--fifos': dict(type=int, default=500, help='Number of'
        ' FIFOs to instantiate in series for this test.')
    }

    net = SbNetwork(cmdline=True, extra_args=extra_args)

    # create the building blocks

    umi_fifo = make_umi_fifo(net)

    # connect them together

    n = net.args.fifos

    umi_fifos = [net.instantiate(umi_fifo) for _ in range(n)]

    for i in range(n - 1):
        net.connect(umi_fifos[i].umi_out, umi_fifos[i + 1].umi_in)

    net.external(umi_fifos[0].umi_in, txrx='umi')
    net.external(umi_fifos[-1].umi_out, txrx='umi')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # interact with the simulation

    umi_loopback(net.intfs['umi'], packets=net.args.packets)


def make_umi_fifo(net):
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

    dut = net.make_dut('umi_fifo', parameters=parameters, interfaces=interfaces,
        clocks=clocks, resets=resets, tieoffs=tieoffs)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.input('umi/rtl/umi_fifo.v', package='umi')

    return dut


if __name__ == '__main__':
    main()
