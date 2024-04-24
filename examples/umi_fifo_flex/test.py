#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import SbDut, UmiTxRx, umi_loopback
import umi


def main():
    # build simulator
    dut = build_testbench()

    # create queues
    umi = UmiTxRx("umi_in.q", "umi_out.q", fresh=True)

    # launch the simulation
    dut.simulate()

    # randomly write data
    umi_loopback(umi, dut.args.n)


def build_testbench():
    extra_args = {
        '-n': dict(type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    }

    idw = 256
    odw = 64
    aw = 64
    cw = 32

    parameters = dict(
        IDW=idw,
        ODW=odw,
        AW=aw,
        CW=cw
    )

    tieoffs = dict(
        bypass="1'b0",
        chaosmode="1'b0",
        fifo_full=None,
        fifo_empty=None,
        vdd="1'b1",
        vss="1'b0"
    )

    interfaces = [
        dict(name='umi_in', type='umi', dw=idw, aw=aw, cw=cw, direction='input'),
        dict(name='umi_out', type='umi', dw=odw, aw=aw, cw=cw, direction='output')
    ]

    clocks = [
        'umi_in_clk',
        'umi_out_clk'
    ]

    resets = [
        'umi_in_nreset',
        'umi_out_nreset'
    ]

    dut = SbDut('umi_fifo_flex', autowrap=True, cmdline=True, extra_args=extra_args,
        parameters=parameters, interfaces=interfaces, clocks=clocks, resets=resets,
        tieoffs=tieoffs)

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.build()

    return dut


if __name__ == '__main__':
    main()
