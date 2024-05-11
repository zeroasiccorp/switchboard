#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import SbDut, random_umi_packet
import umi


def main():
    # build simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate()

    # randomly write data
    umi_in = dut.intfs['umi_in']
    umi_out = dut.intfs['umi_out']

    p = random_umi_packet()
    print(p)

    umi_in[0].send(p)
    print(umi_out[0].recv())


def build_testbench():
    dw = 256
    aw = 64
    cw = 32
    n = 2

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw,
        N=n
    )

    request = 0b1001

    tieoffs = dict(
        mode="2'b00",
        mask=f"{n * n}'d0",
        umi_in_request=f"{n * n}'d{request}"  # TODO: generalize
    )

    interfaces = {
        'umi_in': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input', shape=(n,)),
        'umi_out': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output', shape=(n,))
    }

    resets = ['nreset']

    extra_args = {
        '-n': dict(type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    }

    dut = SbDut('umi_crossbar', autowrap=True, cmdline=True, extra_args=extra_args,
        parameters=parameters, interfaces=interfaces, resets=resets, tieoffs=tieoffs)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.build()

    return dut


if __name__ == '__main__':
    main()
