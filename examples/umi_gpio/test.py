#!/usr/bin/env python3

# Example illustrating how to interact with the umi_endpoint module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from umi import sumi
import random
from switchboard import SbNetwork, sb_path


def main():
    owidth = 512
    iwidth = 512

    net = SbNetwork(cmdline=True, single_netlist=True)

    umi_gpio = net.instantiate(make_umi_gpio(net, owidth=owidth, iwidth=iwidth))
    funcs = net.instantiate(make_funcs(net))

    net.connect(umi_gpio.gpio_out[7:0], funcs.a)
    net.connect(funcs.b, umi_gpio.gpio_out[15:8])
    net.connect(umi_gpio.gpio_in[7:0], funcs.c)
    net.connect(funcs.d, umi_gpio.gpio_in[15:8])
    net.connect(umi_gpio.gpio_out[127:0], funcs.e)
    net.connect(funcs.f, umi_gpio.gpio_in[255:128])
    net.connect(umi_gpio.gpio_in[383:256], funcs.g)
    net.connect(umi_gpio.gpio_out[128], funcs.h)
    net.connect(funcs.i, umi_gpio.gpio_out[129])
    net.connect(umi_gpio.gpio_in[384], funcs.j)
    net.connect(funcs.k, umi_gpio.gpio_in[385])
    net.connect(funcs.m[1:0], 3)
    net.connect(umi_gpio.gpio_out[132:129], funcs.m[5:2])
    net.connect(2, funcs.m[7:6])
    net.connect(funcs.n, 33)
    net.connect(umi_gpio.gpio_in[393:386], funcs.o)
    net.connect(funcs.p, 1)
    net.connect(umi_gpio.gpio_in[394], funcs.q)
    net.connect(funcs.vss, 0)

    net.external(umi_gpio.udev_req, txrx='udev')
    net.external(umi_gpio.udev_resp, txrx='udev')

    # launch the simulation
    net.build()
    net.simulate()

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = net.intfs['udev']
    gpio = umi.gpio(owidth=owidth, iwidth=iwidth, init=0xcafed00d)

    print(f'Initial value: 0x{gpio.o[:]:x}')
    assert gpio.o[:] == 0xcafed00d

    # drive outputs

    gpio.o[7:0] = 22
    print(f'gpio.o[7:0] = {gpio.o[7:0]}')
    assert gpio.o[7:0] == 22

    gpio.o[15:8] = 77
    print(f'gpio.o[15:8] = {gpio.o[15:8]}')
    assert gpio.o[15:8] == 77

    # read first input

    a = gpio.i[7:0]
    print(f'Got gpio.i[7:0] = {a}')
    assert a == 34

    # read second input

    b = gpio.i[15:8]
    print(f'Got gpio.i[15:8] = {b}')
    assert b == 43

    # show that long values work

    stimulus = random.randint(0, (1 << 128) - 1)

    gpio.o[127:0] = stimulus
    print(f'Wrote gpio.o[127:0] = 0x{gpio.o[127:0]:032x}')

    c = gpio.i[255:128]
    print(f'Read gpio.i[255:128] = 0x{c:032x}')
    assert c == stimulus

    d = gpio.i[383:256]
    print(f'Read gpio.i[383:256] = 0x{d:032x}')
    assert d == (~stimulus) & ((1 << 128) - 1)

    for h in [0, 1]:
        for i in [0, 1]:
            gpio.o[128] = h
            gpio.o[129] = i

            j = gpio.i[384]
            k = gpio.i[385]

            print(f'Wrote gpio.o[128]={h}, gpio.o[129]={i}')
            print(f'Read gpio.i[384]={j}, gpio.i[385]={k}')

            assert j == h ^ i
            assert k == h & i

    gpio.o[132:129] = 0b1010
    o = gpio.i[393:386]
    print(f'Wrote gpio.o[132:129]=0b1010, read gpio.i[393:386]={o}')
    assert o == 204

    q = gpio.i[394]
    print(f'Read gpio.i[394]={q}')
    assert q == 1

    print('PASS!')


def make_umi_gpio(net, owidth, iwidth):
    dw = 256
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw,
        OWIDTH=owidth,
        IWIDTH=iwidth
    )

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output'),
        'gpio_out': dict(type='gpio', direction='output', width=owidth),
        'gpio_in': dict(type='gpio', direction='input', width=iwidth)
    }

    resets = ['nreset']

    block = net.make_dut('umi_gpio', parameters=parameters, interfaces=interfaces, resets=resets)

    block.use(sumi)

    block.input(sb_path() / 'verilog' / 'common' / 'umi_gpio.v')

    return block


def make_funcs(net):
    interfaces = {
        'a': dict(type='gpio', direction='input', width=8),
        'b': dict(type='gpio', direction='input', width=8),
        'c': dict(type='gpio', direction='output', width=8),
        'd': dict(type='gpio', direction='output', width=8),
        'e': dict(type='gpio', direction='input', width=128),
        'f': dict(type='gpio', direction='output', width=128),
        'g': dict(type='gpio', direction='output', width=128),
        'h': dict(type='gpio', direction='input', width=1),
        'i': dict(type='gpio', direction='input'),
        'j': dict(type='gpio', direction='output'),
        'k': dict(type='gpio', direction='output', width=1),
        'l': dict(type='gpio', direction='output', width=8),  # intentionally unused
        'm': dict(type='gpio', direction='input', width=8),
        'n': dict(type='gpio', direction='input', width=8),
        'o': dict(type='gpio', direction='output', width=8),
        'p': dict(type='gpio', direction='input'),
        'q': dict(type='gpio', direction='output'),
        'vss': dict(type='gpio', direction='inout')
    }

    tieoffs = {
        'vdd': "1'b1"
    }

    block = net.make_dut('funcs', interfaces=interfaces, tieoffs=tieoffs, clocks=[])

    block.input('funcs.v')

    return block


if __name__ == '__main__':
    main()
