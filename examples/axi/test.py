#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import random
import numpy as np

from switchboard import SbDut, AxiTxRx


def main():
    # build the simulator
    dut = build_testbench()

    # create the queues
    axi = AxiTxRx('axi', data_width=32, addr_width=13, id_width=8, max_beats=dut.args.max_beats)

    # launch the simulation
    dut.simulate()

    # run the test: write to random addresses and read back in a random order

    addr_bytes = (axi.addr_width + 7) // 8

    model = np.zeros((1 << axi.addr_width,), dtype=np.uint8)

    success = True

    for _ in range(dut.args.n):
        addr = random.randint(0, (1 << axi.addr_width) - 1)
        size = random.randint(1, min(dut.args.max_bytes, (1 << axi.addr_width) - addr))

        if random.random() < 0.5:
            #########
            # write #
            #########

            data = np.random.randint(0, 255, size=size, dtype=np.uint8)

            # perform the write
            axi.write(addr, data)
            print(f'Wrote addr=0x{addr:0{addr_bytes * 2}x} data={data}')

            # update local memory model
            model[addr:addr + size] = data
        else:
            ########
            # read #
            ########

            # perform the read
            data = axi.read(addr, size)
            print(f'Read addr=0x{addr:0{addr_bytes * 2}x} data={data}')

            # check against the model
            if not np.array_equal(data, model[addr:addr + size]):
                print('MISMATCH')
                success = False

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


def build_testbench():
    extra_args = {
        '-n': dict(type=int, default=10000, help='Number of'
        ' words to write as part of the test.'),
        '--max-bytes': dict(type=int, default=10, help='Maximum'
        ' number of bytes in any single read/write.'),
        '--max-beats': dict(type=int, default=256, help='Maximum'
        ' number of beats to use in AXI transfers.')
    }

    dut = SbDut(cmdline=True, extra_args=extra_args)

    dut.register_package_source(
        'verilog-axi',
        'git+https://github.com/alexforencich/verilog-axi.git',
        '38915fb'
    )

    dut.input('rtl/axi_ram.v', package='verilog-axi')
    dut.input('testbench.sv')

    dut.add('tool', 'verilator', 'task', 'compile', 'warningoff',
        ['WIDTHEXPAND', 'CASEINCOMPLETE', 'WIDTHTRUNC', 'TIMESCALEMOD'])

    dut.build()

    return dut


if __name__ == '__main__':
    main()
