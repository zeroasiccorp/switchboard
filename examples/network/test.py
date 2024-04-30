#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

import umi
from switchboard import SbDut, SbNetwork

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # create network

    net = SbNetwork(cmdline=True)

    # create the building blocks

    umi_fifo = make_umi_fifo(args=net.args)
    umiram = make_umiram(args=net.args)

    # connect them together

    umi_fifo_in = net.instantiate(umi_fifo)
    umi_fifo_out = net.instantiate(umi_fifo)
    umiram_i = net.instantiate(umiram)

    net.connect(umi_fifo_in.umi_out, umiram_i.udev_req)
    net.connect(umi_fifo_out.umi_in, umiram_i.udev_resp)

    net.external(umi_fifo_in.umi_in, txrx='umi')
    net.external(umi_fifo_out.umi_out, txrx='umi')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    umi = net.intfs['umi']
    umi.write(0x10, np.uint32(0xdeadbeef))
    print(hex(umi.read(0x10, np.uint32)))


def make_umi_fifo(args):
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

    dut = SbDut('umi_fifo', autowrap=True, parameters=parameters, interfaces=interfaces,
        clocks=clocks, resets=resets, tieoffs=tieoffs, args=args)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    return dut


def make_umiram(args):
    dw = 256
    aw = 64
    cw = 32

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input', txrx='umi'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output', txrx='umi')
    }

    dut = SbDut('umiram', autowrap=True, interfaces=interfaces, args=args)

    dut.input(THIS_DIR.parent / 'common' / 'verilog' / 'umiram.sv')

    dut.use(umi)
    dut.add('option', 'library', 'umi')

    dut.build()

    return dut


if __name__ == '__main__':
    main()
