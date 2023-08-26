#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo_flex module
# Copyright (C) 2023 Zero ASIC

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

    tx_orig = [random_umi_packet() for _ in range(n)]

    tx_sets = []  # kept for debug purposes
    tx_hist = []

    tx_set = None
    tx_partial = None

    rx_set = None  # kept for debug purposes
    rx_partial = None

    num_sent = 0

    while (num_sent < n) or (len(tx_hist) > 0):
        # send data
        if num_sent < n:
            txp = tx_orig[num_sent]
            if umi.send(tx_orig[num_sent], blocking=False):
                num_sent += 1

                if tx_partial is not None:
                    if not tx_partial.merge(txp):
                        tx_hist.append(tx_partial)
                        tx_sets.append(tx_set)
                        tx_start_new = True
                    else:
                        tx_set.append(txp)
                        tx_start_new = False
                else:
                    tx_start_new = True

                if tx_start_new:
                    tx_partial = txp
                    tx_set = [txp]

                if num_sent == n:
                    # if this is the last packet, add it to the history
                    # even if the merge was successful
                    tx_hist.append(tx_partial)
                    tx_sets.append(tx_set)

        # receive data
        if len(tx_hist) > 0:
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                # try to merge into an existing partial packet
                if rx_partial is not None:
                    if not rx_partial.merge(rxp):
                        print('=== Mismatch detected ===')
                        for i, p in enumerate(tx_sets[0]):
                            print(f'* TX[{i}] *')
                            print(p)
                        print('---')
                        for i, p in enumerate(rx_set):
                            print(f'* RX[{i}] *')
                            print(p)
                        print('=========================')
                        raise Exception('Mismatch!')
                    else:
                        rx_set.append(rxp)
                else:
                    rx_partial = rxp
                    rx_set = [rxp]

                # at this point it is guaranteed there is something in
                # rx_partial, so compare it to the expected outbound packet
                if rx_partial == tx_hist[0]:
                    tx_hist.pop(0)
                    tx_sets.pop(0)
                    rx_partial = None
                    rx_set = None


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
