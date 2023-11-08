#!/usr/bin/env python3

import time
from argparse import ArgumentParser
from pathlib import Path

from switchboard import SbDut, delete_queues, binary_run

THIS_DIR = Path(__file__).resolve().parent


def main(mode="verilator"):
    # build the simulator
    dut = SbDut(tool=mode, default_main=True)
    dut.input('testbench.sv')
    dut.build(fast=True)

    # clean up old queues if present
    delete_queues(["client2rtl.q", "rtl2client.q"])

    # start client and chip
    # this order yields a smaller waveform file
    client = binary_run(THIS_DIR / 'client')
    time.sleep(1)
    dut.simulate()

    # wait for client and chip to complete
    retcode = client.wait()
    assert retcode == 0


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('mode', default='verilator')
    args = parser.parse_args()

    main(mode=args.mode)
