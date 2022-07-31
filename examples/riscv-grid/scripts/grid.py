#!/usr/bin/env python3

import os
import platform
import atexit
import subprocess
import argparse

from pathlib import Path
from tkinter import E

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
    parser.add_argument('--rows', type=int, default=2)
    parser.add_argument('--cols', type=int, default=3)
    parser.add_argument('--binfile', type=str, default=str(EXAMPLE_DIR / 'riscv' / 'grid.bin'))
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    # launch all the routers
    port = 5555
    routers = []
    for row in range(args.rows):
        routers.append([])
        for col in range(args.cols):
            routers[-1].append({})
            router = routers[-1][-1]
            
            # hub
            router['h_rx'] = port
            port += 1
            router['h_tx'] = port
            port += 1

            # north
            if row != 0:
                router['n_rx'] = routers[row-1][col]['s_tx']
                router['n_tx'] = routers[row-1][col]['s_rx']

            # south
            if row != (args.rows-1):
                router['s_rx'] = port
                port += 1
                router ['s_tx'] = port
                port += 1

            # west
            if col != 0:
                router['w_rx'] = routers[row][col-1]['e_tx']
                router['w_tx'] = routers[row][col-1]['e_rx']
            
            # east
            if col != (args.cols-1):
                router['e_rx'] = port
                port += 1
                router ['e_tx'] = port
                port += 1

    # clean up old queues if present
    for row in range(args.rows):
        for col in range(args.cols):
            for port in routers[row][col].values():
                filename = str(SHMEM_DIR / f'queue-{port}')
                try:
                    os.remove(filename)
                except OSError:
                    pass

    # start routers
    for row in range(args.rows):
        for col in range(args.cols):
            start_router(
                row=row,
                col=col,
                **routers[row][col],
                verbose=args.verbose
            )

    # start chips and client
    for row in range(args.rows):
        for col in range(args.cols):
            if (row==0) and (col==0):
                # client goes here
                continue
            else:
                start_chip(
                    rx_port=routers[row][col]['h_tx'],
                    tx_port=routers[row][col]['h_rx'],
                    verbose=args.verbose
                )

    # client
    client = start_client(
        rows=args.rows,
        cols=args.cols,
        rx_port=routers[0][0]['h_tx'],
        tx_port=routers[0][0]['h_rx'],
        bin = Path(args.binfile).resolve(),
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
