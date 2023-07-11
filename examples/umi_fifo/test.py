#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

from pathlib import Path
from argparse import ArgumentParser
from switchboard import UmiTxRx, random_umi_packet, delete_queue, verilator_run, SbDut


def main(client2rtl='client2rtl.q', rtl2client='rtl2client.q', n=3, fast=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(client2rtl, rtl2client)

    tx_list = []
    rx_list = []

    while (len(tx_list) < n) or (len(rx_list) < n):
        if len(tx_list) < n:
            txp = random_umi_packet()
            if umi.send(txp, blocking=False):
                print('* TX *')
                print(str(txp))
                tx_list.append(txp)

        if len(rx_list) < n:
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                print('* RX *')
                print(str(rxp))
                rx_list.append(rxp)

    assert len(tx_list) == len(rx_list)

    for txp, rxp in zip(tx_list, rx_list):
        assert txp.cmd == rxp.cmd
        assert txp.dstaddr == rxp.dstaddr
        assert txp.srcaddr == rxp.srcaddr
        assert (txp.data == rxp.data).all()


def build_testbench(fast=False):
    dut = SbDut('testbench')

    EX_DIR = Path('..')

    # Set up inputs
    dut.input('testbench.sv')
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
