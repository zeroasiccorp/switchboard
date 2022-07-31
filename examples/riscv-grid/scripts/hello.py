#!/usr/bin/env python3

import os
import platform
import atexit
import subprocess
import argparse

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent
TOP_DIR = EXAMPLE_DIR.parent.parent

# figure out where shared memory queues are located
if platform.system() == 'Darwin':
    SHMEM_DIR = Path('/tmp/boost_interprocess')
else:
    SHMEM_DIR = Path('/dev/shm')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    # clean up old queues if present
    for port in range(5555, 5560+1):
        filename = str(SHMEM_DIR / f'queue-{port}')
        try:
            os.remove(filename)
        except OSError:
            pass

    # routers
    start_router(
        row=0,
        col=0,
        h_rx=5555,
        h_tx=5556,
        e_rx=5558,
        e_tx=5557,
        verbose=args.verbose
    )
    start_router(
        row=0,
        col=1,
        h_rx=5560,
        h_tx=5559,
        w_rx=5557,
        w_tx=5558,
        verbose=args.verbose
    )

    # chip
    start_chip(
        rx_port=5559,
        tx_port=5560,
        verbose=args.verbose
    )

    # client
    client = start_client(
        rows=1,
        cols=2,
        rx_port=5556,
        tx_port=5555,
        bin = EXAMPLE_DIR / 'riscv' / 'hello.bin',
        verbose=args.verbose
    )

    # wait for client to complete
    client.wait()

def start_chip(rx_port, tx_port, verbose=False):
    cmd = []
    cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    cmd += [f'+rx_port={rx_port}']
    cmd += [f'+tx_port={tx_port}']
    cmd = [str(elem) for elem in cmd]

    if verbose:
        print(' '.join(cmd))

    kwargs = {}
    if not verbose:
        kwargs['stdout'] = subprocess.DEVNULL
        kwargs['stderr'] = subprocess.DEVNULL
    p = subprocess.Popen(cmd, **kwargs)

    atexit.register(p.terminate)

def start_router(row=0, col=0, h_rx=0, h_tx=0, n_rx=0, n_tx=0, e_rx=0, e_tx=0,
    s_rx=0, s_tx=0, w_rx=0, w_tx=0, verbose=False):
    cmd = []
    cmd += [TOP_DIR / 'models' / 'router']
    cmd += [row, col, h_rx, h_tx, n_rx, n_tx, e_rx, e_tx, s_rx, s_tx, w_rx, w_tx]
    cmd = [str(elem) for elem in cmd]

    if verbose:
        print(' '.join(cmd))

    p = subprocess.Popen(cmd)
    
    atexit.register(p.terminate)

def start_client(rows, cols, rx_port, tx_port, bin, verbose=False):
    cmd = []
    cmd += [EXAMPLE_DIR / 'cpp' / 'client']
    cmd += [rows, cols, rx_port, tx_port, bin]
    cmd = [str(elem) for elem in cmd]

    if verbose:
        print(' '.join(cmd))

    p = subprocess.Popen(cmd)
    return p

if __name__ == '__main__':
    main()
