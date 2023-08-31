#!/usr/bin/env python3

# Example illustrating how to interact with the umi_splitter module
# Copyright (C) 2023 Zero ASIC

from pathlib import Path
from argparse import ArgumentParser
from switchboard import (UmiTxRx, random_umi_packet, delete_queue,
    verilator_run, SbDut, UmiCmd, umi_opcode)


def main(in_="in.q", out0="out0.q", out1="out1.q", n=3, fast=False):
    # build the simulator
    verilator_bin = build_testbench(fast=fast)

    # clean up old queues if present
    for q in [in_, out0, out1]:
        delete_queue(q)

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi_in = UmiTxRx(in_, "")
    umi_out = [UmiTxRx("", out0), UmiTxRx("", out1)]

    tx_req_list = []
    tx_resp_list = []
    rx_list = [[], []]

    while (((len(tx_req_list) + len(tx_resp_list)) < n)
           or ((len(rx_list[0]) + len(rx_list[1])) < n)):
        # send a packet with a certain probability
        if (len(tx_req_list) + len(tx_resp_list)) < n:
            txp = random_umi_packet(opcode=[UmiCmd.UMI_REQ_WRITE, UmiCmd.UMI_RESP_READ])
            if umi_in.send(txp, blocking=False):
                print('* IN *')
                print(str(txp))
                if umi_opcode(txp.cmd) == UmiCmd.UMI_RESP_READ:
                    tx_resp_list.append(txp)
                else:
                    tx_req_list.append(txp)

        # receive a packet
        if (len(rx_list[0]) + len(rx_list[1])) < n:
            for i in range(2):
                rxp = umi_out[i].recv(blocking=False)
                if rxp is not None:
                    print(f'* OUT #{i} *')
                    print(str(rxp))
                    rx_list[i].append(rxp)

    for list0, list1 in [[tx_resp_list, rx_list[0]], [tx_req_list, rx_list[1]]]:
        assert len(list0) == len(list1)
        for txp, rxp in zip(list0, list1):
            assert txp.cmd == rxp.cmd
            assert txp.dstaddr == rxp.dstaddr
            assert txp.srcaddr == rxp.srcaddr
            assert (txp.data == rxp.data).all()


def build_testbench(fast=False):
    dut = SbDut('testbench')

    EX_DIR = Path('..').resolve()

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
