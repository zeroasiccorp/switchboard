#!/usr/bin/env python3

import os
import platform
import atexit
import subprocess
import argparse

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent

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
    for port in range(5555, 5558+1):
        filename = str(SHMEM_DIR / f'queue-{port}')
        try:
            os.remove(filename)
        except OSError:
            pass

    # routers
    start_router(
        rows=1,
        cols=2,
        rx_ports = [[5555, 5557]],
        tx_ports = [[5556, 5558]],
        verbose=args.verbose
    )

    # chip
    start_chip(
        rx_port=5558,
        tx_port=5557,
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

def start_router(rows, cols, rx_ports, tx_ports, verbose=False):
    cmd = []
    cmd += [EXAMPLE_DIR / 'cpp' / 'router']
    cmd += [rows, cols]
    for i in range(rows):
        for j in range(cols):
            cmd += [rx_ports[i][j], tx_ports[i][j]]
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
