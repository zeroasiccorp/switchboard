#!/usr/bin/env python3

# Example showing how to connect simulations over TCP

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import os

from switchboard import binary_run, SbNetwork, TcpIntf, flip_intf, umi_loopback
from switchboard.cmdline import get_cmdline_args


def main():
    # environment parameters

    max_rate = float(os.environ.get('SB_MAX_RATE', '-1'))

    # design parameters

    dw = 256
    aw = 64
    cw = 32

    # create network

    extra_args = {
        '--packets': dict(type=int, default=1000, help='Number of'
            ' transactions to send into the FIFO during the test.'),
        '--fifos': dict(type=int, default=9, help='Number of'
            ' FIFOs to instantiate in series for this test.'),
        '--fifos-per-sim': dict(type=int, default=3, help='Number of'
            ' FIFOs to include in each simulation.'),
        '--client': dict(type=str, default='localhost'),
        '--server': dict(type=str, default='localhost'),
        '--standalone': dict(action='store_true'),
    }

    args = get_cmdline_args(max_rate=max_rate, extra_args=extra_args)

    net = SbNetwork(args=args)

    if not args.standalone:
        import sys

        subprocess_args = []

        subprocess_args += ['--fast']
        subprocess_args += ['--quiet']
        subprocess_args += ['--tcp']
        subprocess_args += ['--fifos', args.fifos]
        subprocess_args += ['--fifos-per-sim', args.fifos_per_sim]

        env = dict(SB_TCP_IN_PORT='5555', SB_TCP_OUT_PORT='5556', SB_LAST_FIFO='1')
        env.update(os.environ)
        binary_run(sys.executable, ['test.py'] + subprocess_args,
            cwd='../network-fifo-chain', use_sigint=True, env=env)

    intf_i = dict(type='umi', dw=dw, cw=cw, aw=aw, direction='input')
    intf_o = flip_intf(intf_i)

    net.external(
        TcpIntf(intf_i, port=5555, host=net.args.client, mode='client'),
        txrx='umi'
    )

    net.external(
        TcpIntf(intf_o, port=5556, host=net.args.client, mode='client'),
        txrx='umi'
    )

    # launch the simulation

    net.simulate()

    # interact with the simulation

    umi_loopback(net.intfs['umi'], packets=args.packets)


if __name__ == '__main__':
    main()
