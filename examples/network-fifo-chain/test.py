#!/usr/bin/env python3

# Example showing how to wire up various modules using SbNetwork

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import os
import umi
from copy import deepcopy

from switchboard import SbNetwork, umi_loopback, TcpIntf
from switchboard.cmdline import get_cmdline_args

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # environment parameters used when there is TCP bridging

    client = os.environ.get('SB_CLIENT', 'localhost')
    server = os.environ.get('SB_SERVER', '0.0.0.0')
    max_rate = float(os.environ.get('SB_MAX_RATE', '-1'))

    last_fifo = os.environ.get('SB_LAST_FIFO', '1')
    last_fifo = bool(int(last_fifo))

    # create network

    extra_args = {
        '--packets': dict(type=int, default=1000, help='Number of'
            ' transactions to send into the FIFO during the test.'),
        '--fifos': dict(type=int, default=9, help='Number of'
            ' FIFOs to instantiate in series for this test.'),
        '--fifos-per-sim': dict(type=int, default=3, help='Number of'
            ' FIFOs to include in each simulation.'),
        '--tcp': dict(action='store_true', help='Run the simulation with UMI ports'
            ' made available over TCP'),
        '--quiet': dict(action='store_true', help="Don't print debugging information"
            " for TCP bridges.")
    }

    # workaround - need to see what type of simulation we're running
    # (network of simulations, network of networks, single netlist)

    args = get_cmdline_args(max_rate=max_rate, trace=False, extra_args=extra_args)

    assert args.fifos % args.fifos_per_sim == 0, \
        'Number of FIFOs must be divisible by the number of FIFOs per simulation'

    if args.fifos_per_sim in [1, args.fifos]:
        # single network
        args.single_netlist = (args.fifos_per_sim == args.fifos)
        net = SbNetwork(args=args)
        subnet = net
        n = args.fifos
    else:
        # top level network
        args.single_netlist = False
        net = SbNetwork(args=args)

        # subnetwork
        subnet_args = deepcopy(args)
        subnet_args.single_netlist = True
        subnet = SbNetwork(name='subnet', args=subnet_args)

        n = args.fifos_per_sim

    subblock = make_umi_fifo(subnet)

    subblocks = [subnet.instantiate(subblock) for _ in range(n)]

    for i in range(len(subblocks) - 1):
        subnet.connect(subblocks[i].umi_out, subblocks[i + 1].umi_in)

    if n < args.fifos:
        subnet.external(subblocks[0].umi_in, name='umi_in')
        subnet.external(subblocks[-1].umi_out, name='umi_out')

        blocks = [net.instantiate(subnet) for _ in range(args.fifos // args.fifos_per_sim)]

        for i in range(len(blocks) - 1):
            net.connect(blocks[i].umi_out, blocks[i + 1].umi_in)
    else:
        blocks = subblocks

    # external connection depends on whether TCP bridging is being used

    if not args.tcp:
        net.external(blocks[0].umi_in, txrx='umi')
        net.external(blocks[-1].umi_out, txrx='umi')
    else:
        net.connect(
            blocks[0].umi_in,
            TcpIntf(
                port=5555,
                host=server,
                mode='server',
                quiet=args.quiet
            )
        )
        net.connect(
            blocks[-1].umi_out,
            TcpIntf(
                port=5556,
                host=client,
                mode='client' if not last_fifo else 'server',
                quiet=args.quiet
            )
        )

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    if not args.tcp:
        # interact with the simulation

        umi_loopback(net.intfs['umi'], packets=args.packets)
    else:
        # wait for SIGINT

        import sys
        import signal

        def signal_handler(signum, frame):
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        signal.pause()


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
