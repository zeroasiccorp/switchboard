#!/usr/bin/env python3

# Example showing how to connect simulations over TCP

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

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

    net = SbNetwork(cmdline=True, extra_args=extra_args)

    if not net.args.standalone:
        import sys

        args = []

        if (net.max_rate is not None) and (net.max_rate != -1):
            args += ['--max-rate', str(net.max_rate)]

        binary_run(sys.executable, ['ram.py', '--fast'] + args, cwd='ram', use_sigint=True)
        binary_run(sys.executable, ['fifos.py', '--fast'] + args, cwd='fifos', use_sigint=True)

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

    print('PASS!')


if __name__ == '__main__':
    main()
