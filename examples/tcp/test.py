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

    wraddr = 0x10
    wrdata = 0xdeadbeef

    import time

    tick = None

    n_iter = 100

    for _ in range(n_iter):
        umi.write(wraddr, np.uint32(wrdata))
        if tick is None:
            tick = time.time()

        # print(f'Wrote addr=0x{wraddr:x} data=0x{wrdata:x}')

        rdaddr = wraddr

        rddata = umi.read(rdaddr, np.uint32)

        # print(f'Read addr=0x{rdaddr:x} data=0x{rddata:x}')

        assert wrdata == rddata

    tock = time.time()

    print(f'Iterations per second: {n_iter / (tock - tick):0.1f}')

    print('PASS!')


if __name__ == '__main__':
    main()
