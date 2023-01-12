#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
import atexit
import subprocess
import numpy as np
from pathlib import Path
from switchboard import PyUmi, PySbTx, PyUmiPacket, PySbPacket, delete_queue

def main():
    # clean up old queues if present
    for q in ["queue-5555", "queue-5556", "queue-5557"]:
        delete_queue(q)

    chip = start_chip()

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = PyUmi("queue-5555", "queue-5556")
    stop = PySbTx("queue-5557")

    # write 0xBEEFCAFE to address 0x12

    wr_req = PyUmiPacket(
        dstaddr = 0x12,
        size = 2,
        data = np.array([0xBEEFCAFE], dtype=np.uint32).view(np.uint8)
    )

    print("Write Request")
    print(wr_req)
    print()

    umi.write(wr_req)  # note: blocking by default, can disable with blocking=False

    # send request to read address 0x12

    rd_req = PyUmiPacket (
        dstaddr = 0x12,
        size = 2
    )

    print("Read Request")
    print(rd_req)
    print()

    rd_resp = umi.read(rd_req)  # note: blocking, will not return until sucessful

    print("Read Response")
    print(rd_resp)
    print()    

    # stop simulation

    stop.send(PySbPacket())
    chip.wait()

    # declare test as having passed for regression testing purposes

    if (rd_resp.data[:4] == wr_req.data[:4]).all():
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
