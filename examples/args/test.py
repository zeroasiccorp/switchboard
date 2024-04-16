#!/usr/bin/env python3

# Example showing how to pass a custom argument to a simulation binary

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import REMAINDER
from switchboard import SbDut


def main():
    dut = SbDut(cmdline=True, default_main=True)

    parser = dut.get_parser()

    parser.add_argument('remainder', nargs=REMAINDER,
        help='Arguments to pass directly to the simulation.  In this case, the simulation'
        ' accepts plusargs +a+VALUE and +b+VALUE, so you could for example call ./test.py'
        ' +a+12 +b+23.')

    args = parser.parse_args()

    dut.input('testbench.sv')
    dut.build()
    dut.simulate(args=args.remainder).wait()


if __name__ == '__main__':
    main()
