#!/usr/bin/env python3

# Example showing how to set the value of module inputs at runtime without recompilation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from umi import sumi
import numpy as np

from copy import deepcopy

from switchboard import SbNetwork, sb_path
from switchboard.cmdline import get_cmdline_args

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # create network

    extra_args = {
        '--supernet': dict(action='store_true', help='Run simulation using'
            ' a network of single-netlist simulations')
    }

    args = get_cmdline_args(trace=False, extra_args=extra_args)

    net = SbNetwork(args=args)

    if args.supernet:
        subnet_args = deepcopy(args)
        subnet_args.single_netlist = True
        subnet = SbNetwork(name='subnet', args=subnet_args)
    else:
        subnet = net

    umiparam = make_umiparam(subnet)

    umiparam_insts = [subnet.instantiate(umiparam) for _ in range(2)]

    umi_intfs = []

    plusargs = {}
    init_values = []

    for i in range(len(umiparam_insts)):
        if not args.supernet:
            txrx = f'udev_{i}'
            subnet.external(umiparam_insts[i].udev_req, txrx=txrx)
            subnet.external(umiparam_insts[i].udev_resp, txrx=txrx)
            umi_intfs.append(txrx)

            # determine how this umiparam module will be initialized
            init_values.append(10 + (i + 1))
            plusargs[umiparam_insts[i].name] = [('value', init_values[-1])]
        else:
            subnet.external(umiparam_insts[i].udev_req, name=f'udev_req_{i}')
            subnet.external(umiparam_insts[i].udev_resp, name=f'udev_resp_{i}')

    if args.supernet:
        subnet_insts = [net.instantiate(subnet) for _ in range(2)]

        for i in range(len(subnet_insts)):
            plusargs[subnet_insts[i].name] = []
            for j in range(len(umiparam_insts)):
                txrx = f'udev_{i}_{j}'
                net.external(getattr(subnet_insts[i], f'udev_req_{j}'), txrx=txrx)
                net.external(getattr(subnet_insts[i], f'udev_resp_{j}'), txrx=txrx)
                umi_intfs.append(txrx)

                # determine how this umiparam module will be initialized
                init_values.append((10 * (i + 1)) + (j + 1))
                plusargs[subnet_insts[i].name].append(
                    (f'{umiparam_insts[j].name}_value', init_values[-1]))

    # build simulator

    net.build()

    # launch the simulation

    net.simulate(plusargs=plusargs)

    # read back the plusarg-initialized values via UMI

    for umi_intf, init_value in zip(umi_intfs, init_values):
        value = net.intfs[umi_intf].read(0, np.uint32)
        print(f'Read from {umi_intf}: {value}')
        assert value == init_value


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
        'value': dict(type='plusarg', width=32, default=77)
    }

    resets = ['nreset']

    dut = net.make_dut('umiparam', parameters=parameters, interfaces=interfaces, resets=resets)

    dut.use(sumi)

    dut.set('option', 'idir', sb_path() / 'verilog' / 'common')

    dut.input('../common/verilog/umiparam.sv')

    return dut


if __name__ == '__main__':
    main()
