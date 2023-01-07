#!/usr/bin/env python3

import sys
import atexit
import subprocess
import argparse

from switchboard_pybind import delete_queue, init_tx, init_rx, sb_send, sb_recv, PySbPacket

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent

def sb_packet_to_str(p):
    retval = []

    retval += [f'dest: 0x{p.destination:08x}']
    retval += [f'last: {p.flags&1}']
    retval += ['data: {' + ', '.join(f'0x{p.data[i]:02x}' for i in range(32)) + '}']

    return ', '.join(retval)

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    # clean up old queues if present
    for q in ['queue-5555', 'queue-5556']:
        delete_queue(q)

    tx = init_tx("queue-5555")
    rx = init_rx("queue-5556")

    # start chip
    chip = start_chip()

    # form packet
    txp = PySbPacket()
    txp.destination = 0xbeefcafe
    txp.flags = 1
    txp.data = [i&0xff for i in range(32)]  # must set whole array at once

    # send packet

    while not sb_send(tx, txp):
        pass
    print("*** TX packet ***")
    print(sb_packet_to_str(txp))

    # receive packet
    rxp = PySbPacket()
    while not sb_recv(rx, rxp):
        pass

    print("*** RX packet ***")
    print(sb_packet_to_str(rxp))

    success = True
    for i in range(32):
        if rxp.data[i] != (txp.data[i] + 1):
            success = False

    # send a packet that will end the test

    txp.data = [0xff for _ in range(32)]  # must set whole array at once
    while not sb_send(tx, txp):
        pass

    # wait for chip to complete
    chip.wait()

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)

def start_chip():
    cmd = []
    cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    cmd += ['+trace']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)

    return p

if __name__ == '__main__':
    main()
