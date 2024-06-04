#!/usr/bin/env python3

# Example showing how to set the value of module inputs at runtime without recompilation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import umi
import numpy as np

from switchboard import SbNetwork, sb_path

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    net = SbNetwork(cmdline=True)

    umiparam = make_umiparam(net)

    umiparam_0 = net.instantiate(umiparam)
    umiparam_1 = net.instantiate(umiparam)

    net.external(umiparam_0.udev_req, txrx='udev0')
    net.external(umiparam_0.udev_resp, txrx='udev0')

    net.external(umiparam_1.udev_req, txrx='udev1')
    net.external(umiparam_1.udev_resp, txrx='udev1')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate(
        init=[
            (umiparam_0.value, 12),
            (umiparam_1.value, 34)
        ]
    )

    print(net.intfs['udev0'].read(0, np.uint32))
    print(net.intfs['udev1'].read(0, np.uint32))


def make_umiparam(net):
    dw = 32
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw
    )

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output'),
        'value': dict(type='init', width=32, default=77)
    }

    resets = ['nreset']

    dut = net.make_dut('umiparam', parameters=parameters, interfaces=interfaces, resets=resets)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.set('option', 'idir', sb_path() / 'verilog' / 'common')

    dut.input('../common/verilog/umiparam.sv')

    return dut


if __name__ == '__main__':
    main()
