#!/usr/bin/env python

from ast import arg
import sys
import os
import atexit
import subprocess
import argparse
import time
import shutil

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent

def main(start_port=5555, n_chips=10):
    parser = argparse.ArgumentParser()
    parser.add_argument('--sim', default='verilator')
    args = parser.parse_args()

    # create the files of interest
    for k in range(n_chips+1):
        name = f'/tmp/feeds-{start_port+k}'
        if os.path.exists(name):
            os.remove(name)
        with open(name, 'wb') as f:
            f.truncate(262144)
        os.chmod(name, 0o666)

    # chips
    for k in range(n_chips):
        p = start_chip(
            rx_port=start_port+k,
            tx_port=start_port+k+1,
            sim=args.sim
        )
        atexit.register(p.terminate)

    # client
    client = start_client(
        tx_port=start_port,
        rx_port=start_port+n_chips,
        bin = THIS_DIR / 'build' / 'sw' / 'daisy.bin'
    )

    # wait for client to complete
    tic = time.time()
    client.wait()
    toc = time.time()

    print(f"Took {1e3*(toc-tic):0.3f} ms")

def start_chip(rx_port, tx_port, sim='verilator'):
    cmd = []
    if sim == 'verilator':
        cmd += [THIS_DIR / 'vpidpi' / 'verilator_dpi' / 'Vtestbench']
    elif sim == 'iverilog':
        cmd += ['vvp']
        cmd += ['-n']
        cmd += ['-M', THIS_DIR / 'vpidpi' / 'iverilog_vpi']
        cmd += ['-m', 'zmq_vpi']
        cmd += [THIS_DIR / 'vpidpi' / 'iverilog_vpi' / 'testbench.vvp']
    else:
        raise Exception(f'Unknown simulator: {sim}')
    cmd += [f'+rx_port={rx_port}']
    cmd += [f'+tx_port={tx_port}']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #p = subprocess.Popen(cmd)
    return p

def start_client(rx_port, tx_port, bin):
    cmd = []
    cmd += [THIS_DIR / 'zmq_client']
    cmd += [rx_port]
    cmd += [tx_port]
    cmd += [bin]
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)
    return p

if __name__ == '__main__':
    main()
