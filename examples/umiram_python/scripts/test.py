#!/usr/bin/env python3

import os
import sys
import atexit
import subprocess
import argparse

from pathlib import Path

from switchboard import UMI, SBTX, PyUmiPacket, PySbPacket, umi_opcode_to_str

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent
SHMEM_DIR = EXAMPLE_DIR

def print_packet_details(p: PyUmiPacket):
    # print details
    print("dstaddr: " + f"0x{p.dstaddr:016x}")
    print("size:    " + str(p.size))
    print("data:    " + "[" + ", ".join([f"0x{elem:02x}" for elem in p.data[:(1<<p.size)]]) + "]")

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    # clean up old queues if present
    for port in [5555, 5556, 5557]:
        filename = str(SHMEM_DIR / f'queue-{port}')
        try:
            os.remove(filename)
        except OSError:
            pass

    chip = start_chip()

    umi = UMI()
    umi.init("queue-5555", "queue-5556")

    stop = SBTX()
    stop.init("queue-5557")

    txp = PyUmiPacket()

    # write 0xBEEFCAFE to address 0x12
    txp.data = [0xBE, 0xEF, 0xCA, 0xFE][::-1] + [0]*28
    txp.dstaddr = 0x12
    txp.size = 2
    umi.write(txp)

    print("TX packet")
    print_packet_details(txp)
    print()

    # send request to read address 0x12
    rxp = PyUmiPacket()
    rxp.dstaddr = 0x12
    rxp.size = 2
    umi.read(rxp)

    print("RX packet")
    print_packet_details(rxp)
    print()    

    p = PySbPacket()
    stop.send_blocking(p)

    chip.wait()

    if rxp.data[:4] == txp.data[:4]:
        print('PASS!')
        sys.exit(0)
    else:
        print('FAIL')
        sys.exit(1)

def start_chip(trace=True):
    cmd = []
    cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    if trace:
        cmd += ['+trace']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)

    return p

if __name__ == '__main__':
    main()
