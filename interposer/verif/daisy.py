#!/usr/bin/env python

import sys
import atexit
import subprocess

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent

def main(start_port=5555, n_chips=10):
    # chips
    for k in range(n_chips):
        p = start_chip(
            rx_port=start_port+k,
            tx_port=start_port+k+1
        )
        atexit.register(p.terminate)

    # client
    client = start_client(
        tx_port=start_port,
        rx_port=start_port+n_chips,
        bin = THIS_DIR / 'build' / 'sw' / 'daisy.bin'
    )

    # wait for client to complete
    client.wait()

def start_chip(rx_port, tx_port):
    cmd = []
    cmd += [THIS_DIR / 'vpidpi' / 'verilator_dpi' / 'Vtestbench']
    cmd += [f'+rx_port={rx_port}']
    cmd += [f'+tx_port={tx_port}']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p

def start_client(rx_port, tx_port, bin):
    cmd = []
    cmd += [sys.executable]
    cmd += [THIS_DIR / 'zmq_client.py']
    cmd += ['--rx_port', rx_port]
    cmd += ['--tx_port', tx_port]
    cmd += ['--bin', bin]
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)
    return p

if __name__ == '__main__':
    main()