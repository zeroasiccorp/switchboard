#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
import atexit
import subprocess
import numpy as np
from pathlib import Path
from switchboard import UmiTxRx, PySbTx, PySbPacket, delete_queue

def main():
    # clean up old queues if present
    for q in ["queue-5555", "queue-5556", "queue-5557"]:
        delete_queue(q)

    chip = start_chip()

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx("queue-5555", "queue-5556")
    stop = PySbTx("queue-5557")

    # write 0xbeefcafe to address 0x12

    wr_addr = 0x12
    wr_data = np.uint32(0xbeefcafe)
    umi.write(wr_addr, wr_data)
    print(f"Wrote to 0x{wr_addr:02x}: 0x{wr_data:08x}")

    # read data from address 0x12

    rd_addr = wr_addr
    rd_data = umi.read(rd_addr, np.uint32)
    print(f"Read from 0x{rd_addr:02x}: 0x{rd_data:08x}")

    # stop simulation

    stop.send(PySbPacket())
    chip.wait()

    # declare test as having passed for regression testing purposes

    if rd_data == wr_data:
        print('PASS!')
        sys.exit(0)
    else:
        print('FAIL')
        sys.exit(1)

def start_chip(trace=True):
    this_dir = Path(__file__).resolve().parent
    example_dir = this_dir.parent

    cmd = []
    cmd += [example_dir / 'verilator' / 'obj_dir' / 'Vtestbench']
    if trace:
        cmd += ['+trace']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)

    return p

if __name__ == '__main__':
    main()
