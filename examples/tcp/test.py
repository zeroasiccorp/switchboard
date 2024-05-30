#!/usr/bin/env python3

# Example showing how to connect simulations over TCP

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import os
import numpy as np

from switchboard import binary_run, SbNetwork, TcpIntf, flip_intf


def main():
    # parameters

    dw = 256
    aw = 64
    cw = 32

    # create network

    extra_args = {
        '--client': dict(type=str, default='localhost'),
        '--server': dict(type=str, default='0.0.0.0'),
        '--standalone': dict(action='store_true'),
    }

    max_rate = float(os.environ.get('SB_MAX_RATE', '-1'))
    net = SbNetwork(max_rate=max_rate, cmdline=True, extra_args=extra_args)

    if not net.args.standalone:
        import sys

        args = []

        args += ['--fast']

        args += ['--quiet']

        binary_run(sys.executable, ['ram.py'] + args, cwd='ram', use_sigint=True)
        binary_run(sys.executable, ['fifos.py'] + args, cwd='fifos', use_sigint=True)

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

    umi = net.intfs['umi']

    import time

    tick = None

    n_iter = 100

    for _ in range(n_iter):
        wraddr = np.random.randint(0, 8, dtype=np.uint32) << 4
        wrdata = np.random.randint(0, 1 << 32, dtype=np.uint32)

        umi.write(wraddr, np.uint32(wrdata))

        rdaddr = wraddr

        rddata = umi.read(rdaddr, np.uint32)

        assert wrdata == rddata

        if tick is None:
            # start measuring time after the first iteration to avoid including
            # the time needed to start up simulators
            tick = time.time()

    tock = time.time()

    iters_per_second = (n_iter - 1) / (tock - tick)
    print(f'Iterations per second: {(n_iter - 1) / (tock - tick):0.1f}')

    est_latency = (1 / iters_per_second) / 8
    if est_latency < 1e-6:
        est_latency = f'{est_latency * 1e9:0.1f} ns'
    elif est_latency < 1e-3:
        est_latency = f'{est_latency * 1e6:0.1f} us'
    elif est_latency < 1:
        est_latency = f'{est_latency * 1e3:0.1f} ms'
    else:
        est_latency = f'{est_latency:0.1f} s'

    print(f'Estimated latency: {est_latency}')

    print('PASS!')


if __name__ == '__main__':
    main()
