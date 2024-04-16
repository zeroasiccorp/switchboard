#!/usr/bin/env python3

# Example demonstrating the built-in Switchboard router

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from switchboard import switchboard, delete_queue, binary_run, SbDut

THIS_DIR = Path(__file__).resolve().parent


def main(aq="5555", bq="5556", cq="5557", dq="5558"):
    # build the simulator
    dut = SbDut(cmdline=True)
    dut.input('testbench.sv')
    dut.build()

    # clean up old queues if present
    for q in [aq, bq, cq, dq]:
        delete_queue(f'queue-{q}')

    # start chip simulation
    dut.simulate()

    # start router
    start_router(aq=aq, bq=bq, cq=cq, dq=dq)

    # wait for client to complete
    client = binary_run(THIS_DIR / 'client')
    client.wait()


def start_router(aq, bq, cq, dq):
    args = []
    args += ['--tx', bq, cq]
    args += ['--rx', aq, dq]
    args += ['--route', '0:5556', '1:5557']

    return binary_run(bin=switchboard.path() / 'cpp' / 'router', args=args)


if __name__ == '__main__':
    main()
