#!/usr/bin/env python3

# Example demonstrating a sequence of Switchboard packets

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import time

from pathlib import Path
from switchboard import delete_queues, binary_run, SbDut


def main():
    # build the simulator
    dut = SbDut(cmdline=True, default_main=True)
    dut.input('testbench.sv')
    dut.build()

    # clean up old queues if present
    delete_queues(['client2rtl.q', 'rtl2client.q'])

    # start client and chip
    # this order yields a smaller waveform file
    client = binary_run(Path('client').resolve())
    time.sleep(1)
    chip = dut.simulate()

    # wait for client and chip to complete
    client.wait()
    chip.wait()


if __name__ == '__main__':
    main()
