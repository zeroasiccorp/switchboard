#!/usr/bin/env python3

# Example illustrating mixed-signal simulation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import SbDut


def main():
    ###############################
    # create the simulator object #
    ###############################

    dut = SbDut(cmdline=True)

    dut.input('testbench.sv')

    #################################
    # specify the analog subcircuit #
    #################################

    vdd = 1.0

    params = dict(
        vol=0,
        voh=vdd,
        vil=0.2 * vdd,
        vih=0.8 * vdd
    )

    dut.input_analog(
        'mycircuit.cir',
        pins=[
            dict(name='a', type='input', **params),
            dict(name='b[1:0]', type='input', **params),
            dict(name='y', type='output', **params),
            dict(name='z[1:0]', type='output', **params),
            dict(name='vss', type='constant', value=0)
        ]
    )

    # build the simulator
    dut.build()

    # start the simulator
    chip = dut.simulate()

    # wait for the simulation to complete
    chip.wait()


if __name__ == '__main__':
    main()
