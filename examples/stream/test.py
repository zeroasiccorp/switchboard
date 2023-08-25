#!/usr/bin/env python3

# Example demonstrating a sequence of Switchboard packets
# Copyright (C) 2023 Zero ASIC

import time

from pathlib import Path
from switchboard import delete_queue, verilator_run, binary_run, SbDut

THIS_DIR = Path(__file__).resolve().parent


def main():
    # build the simulator
    verilator_bin = build_testbench()

    # clean up old queues if present
    for q in ['client2rtl.q', 'rtl2client.q']:
        delete_queue(q)

    # start client and chip
    # this order yields a smaller VCD
    client = binary_run(THIS_DIR / 'client')
    time.sleep(1)
    chip = verilator_run(verilator_bin)

    # wait for client and chip to complete
    client.wait()
    chip.wait()


def build_testbench():
    dut = SbDut('testbench')

    EX_DIR = Path('..').resolve()

    # Set up inputs
    dut.input('testbench.sv')
    dut.input(EX_DIR / 'common' / 'verilator' / 'testbench.cc')

    # Settings
    dut.set('option', 'trace', True)  # enable VCD (TODO: FST option)

    # Build simulator
    dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    main()
