#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module
# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from switchboard import SbDut, UmiTxRx, delete_queue, verilator_run, random_umi_packet


def main(client2rtl="client2rtl.q", rtl2client="rtl2client.q", n=3, fast=False):
    # build simulator
    verilator_bin = build_testbench(fast=fast)

    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # instantiate TX and RX queues
    umi = UmiTxRx(client2rtl, rtl2client)

    # randomly write data

    q = []
    partial = None
    num_sent = 0
    num_recv = 0

    while (num_sent < n) or (num_recv < n):
        # send data
        if num_sent < n:
            txp = random_umi_packet()
            if umi.send(txp, blocking=False):
                print('*** SENT ***')
                print(txp)
                q.append(txp.data)
                num_sent += 1

        # receive data
        if num_recv < n:
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                print("*** RECEIVED ***")
                print(rxp)

                if partial is None:
                    partial = rxp.data
                else:
                    partial = np.concatenate((partial, rxp.data))

                if (len(q) > 0) and (len(q[0]) == len(partial)):
                    assert (q[0] == partial).all(), "Data mismatch"
                    q.pop(0)
                    partial = None
                    num_recv += 1


def build_testbench(fast=False):
    dut = SbDut('testbench')

    EX_DIR = Path('..').resolve()

    # Set up inputs
    dut.input('testbench.sv')
    dut.input(EX_DIR / 'common' / 'verilog' / 'umiram.sv')
    dut.input(EX_DIR / 'common' / 'verilator' / 'testbench.cc')
    for option in ['ydir', 'idir']:
        dut.add('option', option, EX_DIR / 'deps' / 'umi' / 'umi' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'ramlib' / 'rtl')
        dut.add('option', option, EX_DIR / 'deps' / 'lambdalib' / 'stdlib' / 'rtl')

    # Verilator configuration
    vlt_config = EX_DIR / 'common' / 'verilator' / 'config.vlt'
    dut.set('tool', 'verilator', 'task', 'compile', 'file', 'config', vlt_config)

    # Settings
    dut.set('option', 'trace', True)  # enable VCD (TODO: FST option)

    result = None

    if fast:
        result = dut.find_result('vexe', step='compile')

    if result is None:
        dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', type=int, default=3, help='Number of'
        ' transactions to send into the FIFO during the test.')
    parser.add_argument('--fast', action='store_true', help='Do not build'
        ' the simulator binary if it has already been built.')
    args = parser.parse_args()

    main(n=args.n, fast=args.fast)
