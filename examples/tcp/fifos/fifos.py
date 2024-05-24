#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import signal

import umi
from switchboard import SbNetwork, TcpIntf, flip_intf


def main():
    # parameters

    dw = 256
    aw = 64
    cw = 32

    # create network

    extra_args = {
        '--client': dict(type=str, default='localhost'),
        '--server': dict(type=str, default='localhost')
    }

    net = SbNetwork(cmdline=True, extra_args=extra_args)

    # create the building blocks

    umi_fifo = make_umi_fifo(net, dw=dw, aw=aw, cw=cw)
    umi_fifo_in = net.instantiate(umi_fifo)

    net.connect(
        TcpIntf(port=5555, host=net.args.server, mode='server'),
        umi_fifo_in.umi_in
    )

    intf_i = dict(type='umi', dw=dw, cw=cw, aw=aw, direction='input')
    intf_o = flip_intf(intf_i)

    net.connect(
        TcpIntf(intf_i, port=5556, host=net.args.server, mode='server'),
        TcpIntf(intf_o, port=5557, host=net.args.client, mode='client')
    )

    net.connect(
        umi_fifo_in.umi_out,
        TcpIntf(port=5558, host=net.args.client, mode='client')
    )

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # wait for SIGINT

    def signal_handler(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    signal.pause()


def make_umi_fifo(net, dw, aw, cw):
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
