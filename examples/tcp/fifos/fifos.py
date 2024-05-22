#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

import umi
from switchboard import SbNetwork, TcpIntf


def main():
    # create network

    net = SbNetwork(cmdline=True)

    # create the building blocks

    umi_fifo = make_umi_fifo(net)
    umi_fifo_in = net.instantiate(umi_fifo)
    umi_fifo_out = net.instantiate(umi_fifo)

    net.connect(umi_fifo_in.umi_out, TcpIntf(port=5555))
    net.connect(umi_fifo_out.umi_in, TcpIntf(port=5556))

    net.external(umi_fifo_in.umi_in, txrx='umi')
    net.external(umi_fifo_out.umi_out, txrx='umi')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # interact with the simulation

    umi = net.intfs['umi']

    wraddr = 0x10
    wrdata = 0xdeadbeef

    umi.write(wraddr, np.uint32(wrdata))

    print(f'Wrote addr=0x{wraddr:x} data=0x{wrdata:x}')

    rdaddr = wraddr

    rddata = umi.read(rdaddr, np.uint32)

    print(f'Read addr=0x{rdaddr:x} data=0x{rddata:x}')

    assert wrdata == rddata


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
