#!/usr/bin/env python3

# Example showing how to set the value of module inputs at runtime without recompilation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import umi
import numpy as np

from switchboard import SbNetwork

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    net = SbNetwork(cmdline=True)

    umiparam = make_umiparam(net)

    umiparam_0 = net.instantiate(umiparam, tieoffs=dict(value=12))
    umiparam_1 = net.instantiate(umiparam, tieoffs=dict(value=34))

    net.external(umiparam_0.udev_req, txrx='udev0')
    net.external(umiparam_0.udev_resp, txrx='udev0')

    net.external(umiparam_1.udev_req, txrx='udev1')
    net.external(umiparam_1.udev_resp, txrx='udev1')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

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

    tieoffs = dict(
        value=dict(value=77, width=32, per_instance=True, plusarg='value')
    )

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output')
    }

    resets = ['nreset']

    dut = net.make_dut('umiparam', parameters=parameters, interfaces=interfaces,
        resets=resets, tieoffs=tieoffs)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.input('../common/verilog/umiparam.sv')

    return dut


if __name__ == '__main__':
    main()
