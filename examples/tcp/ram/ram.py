#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import os
import sys
import signal

import umi
from switchboard import SbNetwork, TcpIntf

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # parameters

    server = os.environ.get('SB_SERVER', '0.0.0.0')
    max_rate = float(os.environ.get('SB_MAX_RATE', '-1'))

    # create network

    extra_args = {
        '--quiet': dict(action='store_true')
    }

    net = SbNetwork(max_rate=max_rate, cmdline=True, extra_args=extra_args)

    quiet = net.args.quiet

    # create the building blocks

    umiram = net.instantiate(make_umiram(net))

    net.connect(umiram.udev_req, TcpIntf(port=5558, host=server, mode='server', quiet=quiet))
    net.connect(umiram.udev_resp, TcpIntf(port=5557, host=server, mode='server', quiet=quiet))

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # wait for SIGINT

    def signal_handler(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    signal.pause()


def make_umiram(net):
    dw = 256
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw
    )

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output')
    }

    dut = net.make_dut('umiram', parameters=parameters, interfaces=interfaces)

    dut.use(umi)
    dut.add('option', 'library', 'umi')

    dut.input(THIS_DIR.parent.parent / 'common' / 'verilog' / 'umiram.sv', package='umi')

    return dut


if __name__ == '__main__':
    main()
