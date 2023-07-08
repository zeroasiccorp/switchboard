#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import numpy as np
from pathlib import Path
from random import random, randint
from switchboard import UmiTxRx, PyUmiPacket, delete_queue, verilator_run, SbDut


def main(client2rtl='client2rtl.q', rtl2client='rtl2client.q', n=3):
    # build the simulator
    verilator_bin = build_testbench()

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
    n_sent = 0
    n_recv = 0

    while (n_sent < n) or (n_recv < n):
        if (n_sent < n):
            cmd = 0x3 | (1 << 22) | (1 << 23)
            dstaddr = randint(0, (1 << 64) - 1)
            srcaddr = randint(0, (1 << 64) - 1)
            data = np.random.randint(0, 256, (1,), dtype=np.uint8)

            txp = PyUmiPacket(cmd=cmd, dstaddr=dstaddr, srcaddr=srcaddr, data=data)
            if umi.send(txp, blocking=False):
                tx_list.append(txp)
                print('* TX *')
                print(str(txp))
                n_sent += 1

        if (n_recv < n) and (random() > 0.9):
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                print('* RX *')
                print(str(rxp))
                rx_list.append(rxp)
                n_recv += 1

    assert len(tx_list) == len(rx_list)

    for txp, rxp in zip(tx_list, rx_list):
        assert txp.cmd == rxp.cmd
        assert txp.dstaddr == rxp.dstaddr
        assert txp.srcaddr == rxp.srcaddr
        assert txp.data == rxp.data


def build_testbench():
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

    # Build simulator
    dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    main()
