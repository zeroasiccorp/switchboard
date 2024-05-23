#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

import umi
from switchboard import SbNetwork, TcpIntf


def main():
    # parameters

    dw = 256
    aw = 64
    cw = 32

    # create network

    net = SbNetwork(cmdline=True, extra_args={'--host': dict(type=str, default='localhost')})

    # create the building blocks

    umi_fifo = make_umi_fifo(net, dw=dw, aw=aw, cw=cw)
    umi_fifo_in = net.instantiate(umi_fifo)

    net.connect(umi_fifo_in.umi_out, TcpIntf(port=5555, host=net.args.host, quiet=False))

    net.external(umi_fifo_in.umi_in, txrx='umi')

    # just for illustrative purposes, don't connect a FIFO to
    # the UMI stream on port 5556, and instead connect that
    # port directly to a UmiTxRx block

    intf = dict(type='umi', dw=dw, cw=cw, aw=aw, direction='output')
    tcp_intf = TcpIntf(intf, port=5556, quiet=False)
    net.external(tcp_intf, txrx='umi')

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
