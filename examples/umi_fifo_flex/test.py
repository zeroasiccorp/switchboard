#!/usr/bin/env python3

# Example illustrating how UMI packets are handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from switchboard import (SbDut, UmiTxRx, PyUmiPacket, delete_queue,
    verilator_run, umi_pack, UmiCmd)


def build_testbench():
    dut = SbDut('testbench')

    EX_DIR = Path('..')

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

    # Build simulator
    dut.run()

    return dut.find_result('vexe', step='compile')


def main(client2rtl="client2rtl.q", rtl2client="rtl2client.q", n=3):
    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    # build simulator
    verilator_bin = build_testbench()

    # launch the simulation
    verilator_run(verilator_bin, plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(client2rtl, rtl2client)

    offset = 0
    runs = 3
    txp = None
    rx_count = 0
    num_sent = 0
    next_expected = 1

    while num_sent<runs:
        if txp is None:
            atype = 0
            size = 3
            len_ = 1
            eom = 1
            eof = 1
            cmd = umi_pack(UmiCmd.UMI_REQ_WRITE, atype, size, len_, eom, eof)
            dstaddr = 0
            srcaddr = 0
            data = np.array([1+offset, 2+offset], dtype=np.uint64)
            offset += 2
            txp = PyUmiPacket(cmd, dstaddr, srcaddr, data)
        if umi.send(txp, blocking=False):
            txp = None
            num_sent += 1

        rxp = umi.recv(blocking=False)
        if rxp is not None:
            print(rxp)
            assert rxp.data.view(np.uint64)[0] == next_expected
            next_expected += 1
            rx_count += 1

    while rx_count < 2*runs:
        rxp = umi.recv()
        print(rxp)
        assert rxp.data.view(np.uint64)[0] == next_expected
        next_expected += 1
        rx_count += 1

    # atype = 0
    # size = 3
    # len_ = 1
    # eom = 1
    # eof = 1
    # cmd = umi_pack(UmiCmd.UMI_REQ_READ, atype, size, len_, eom, eof)
    # dstaddr = 0
    # srcaddr = 0
    # data = None
    # p = PyUmiPacket(cmd, dstaddr, srcaddr, data)
    # umi.send(p)

    # for _ in range(2):
    #     print(umi.recv())

    # atype = 0
    # size = 3
    # len_ = 1
    # eom = 1
    # eof = 1
    # cmd = umi_pack(UmiCmd.UMI_RESP_WRITE, atype, size, len_, eom, eof)
    # dstaddr = 0
    # srcaddr = 0
    # data = None
    # p = PyUmiPacket(cmd, dstaddr, srcaddr, data)
    # umi.send(p)

    # for _ in range(2):
    #     print(umi.recv())


if __name__ == '__main__':
    main()
