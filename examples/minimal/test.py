#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import time
from pathlib import Path

from switchboard import SbDut, delete_queues, binary_run

THIS_DIR = Path(__file__).resolve().parent


def main():
    # build the simulator
    dut = SbDut(cmdline=True, default_main=True)
    dut.input('testbench.sv')
    dut.build(fast=True)

    # clean up old queues if present
    delete_queues(["to_rtl.q", "from_rtl.q"])

    # start client and chip
    # this order yields a smaller waveform file
    client = binary_run(THIS_DIR / 'client')
    time.sleep(1)
    dut.simulate()

    # wait for client and chip to complete
    retcode = client.wait()
    assert retcode == 0


if __name__ == '__main__':
    main()
