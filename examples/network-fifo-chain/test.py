#!/usr/bin/env python3

# Example showing how to wire up various modules using SbNetwork

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import umi
from switchboard import SbNetwork, umi_loopback
from switchboard.cmdline import get_cmdline_args

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # create network

    extra_args = {
        '--packets': dict(type=int, default=1000, help='Number of'
        ' transactions to send into the FIFO during the test.'),
        '--fifos': dict(type=int, default=500, help='Number of'
        ' FIFOs to instantiate in series for this test.'),
        '--fifos-per-sim': dict(type=int, default=1, help='Number of'
        ' FIFOs to include in each simulation.')
    }

    # workaround - need to see what type of simulation we're running
    # (network of simulations, network of networks, single netlist)

    args = get_cmdline_args(extra_args=extra_args)

    assert args.fifos % args.fifos_per_sim == 0, \
        'Number of FIFOs must be divisible by the number of FIFOs per simulation'

    if args.fifos_per_sim in [1, args.fifos]:
        # single network
        net = SbNetwork(cmdline=True, single_netlist=args.fifos_per_sim == args.fifos)
        subnet = net
        n = args.fifos
    else:
        # network of networks
        net = SbNetwork(cmdline=True, single_netlist=False)
        subnet = SbNetwork(name='subnet', cmdline=True, single_netlist=True)
        n = args.fifos_per_sim

    subblock = make_umi_fifo(subnet)

    subblocks = [subnet.instantiate(subblock) for _ in range(n)]

    for i in range(len(subblocks) - 1):
        subnet.connect(subblocks[i].umi_out, subblocks[i + 1].umi_in)

    if n < args.fifos:
        umi_in = subnet.external(subblocks[0].umi_in)
        umi_out = subnet.external(subblocks[-1].umi_out)

        blocks = [net.instantiate(subnet) for _ in range(args.fifos // args.fifos_per_sim)]

        for i in range(len(blocks) - 1):
            net.connect(getattr(blocks[i], umi_out), getattr(blocks[i + 1], umi_in))
    else:
        blocks = subblocks
        umi_in = 'umi_in'
        umi_out = 'umi_out'

    net.external(getattr(blocks[0], umi_in), txrx='umi')
    net.external(getattr(blocks[-1], umi_out), txrx='umi')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # interact with the simulation

    umi_loopback(net.intfs['umi'], packets=args.packets)


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
