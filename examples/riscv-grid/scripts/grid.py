#!/usr/bin/env python3

import os
import time
import platform
import atexit
import subprocess
import argparse
import multiprocessing

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
    parser.add_argument('--extra_time', type=float, default=None)
    parser.add_argument('--yield_every', type=int, default=None)
    parser.add_argument('--params', type=int, nargs='+', default=None)
    args = parser.parse_args()

    # set defaults
    if args.yield_every is None:
        if (args.rows * args.cols) > multiprocessing.cpu_count():
            # number of active threads is (rows*cols) - 1, since the client mostly yields
            # then add one extra thread for the router process, which gets us back to rows*cols
            # we need to be careful if the number of active threads is greater than the hardware
            # thread count, since in that case the latency is dominated by how often threads
            # switch.  in the extreme case, yield_every=1, the verilator sims switch every clock
            # cycle, which provides low latency, but terrible throughput due to the context
            # switch overhead.  a good value for yield_every can be chosen by increasing it
            # simulation throughput is reasonably close to the performance without explicit
            # yielding (say within 10-20% of that value).  the default here seems to be reasonable
            # for simulations running in the 1-5 MHz range.
            args.yield_every = 250

    # set up connections
    port = 5555
    rx_connections = []
    tx_connections = []
    for row in range(args.rows):
        rx_connections.append([])
        tx_connections.append([])
        for col in range(args.cols):
            rx_connections[-1].append(port)
            port += 1

            tx_connections[-1].append(port)
            port += 1

    # clean up old queues if present
    for row in range(args.rows):
        for col in range(args.cols):
            for port in [rx_connections[row][col], tx_connections[row][col]]:
                filename = str(SHMEM_DIR / f'queue-{port}')
                try:
                    os.remove(filename)
                except OSError:
                    pass

    # start router
    start_router(
        rows=args.rows,
        cols=args.cols,
        rx_ports = tx_connections,
        tx_ports = rx_connections,
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
                    rx_port=rx_connections[row][col],
                    tx_port=tx_connections[row][col],
                    yield_every=args.yield_every,
                    verbose=args.verbose
                )

    # client
    client = start_client(
        rows=args.rows,
        cols=args.cols,
        rx_port=rx_connections[0][0],
        tx_port=tx_connections[0][0],
        bin = Path(args.binfile).resolve(),
        params = args.params,
        verbose=args.verbose
    )

    # wait for client to complete
    client.wait()

    # wait extra time (perhaps too see certain values printed)
    if args.extra_time is not None:
        time.sleep(args.extra_time)

def start_chip(rx_port, tx_port, yield_every=None, vcd=False, verbose=False):
    cmd = []
    cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    cmd += [f'+rx_port={rx_port}']
    cmd += [f'+tx_port={tx_port}']
    if vcd:
        cmd += [f'+vcd']
    if yield_every is not None:
        cmd += [f'+yield_every={yield_every}']
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

def start_client(rows, cols, rx_port, tx_port, bin, params=None, verbose=False):
    cmd = []
    cmd += [EXAMPLE_DIR / 'cpp' / 'client']
    cmd += [rows, cols, rx_port, tx_port, bin]
    if params is not None:
        cmd += params
    cmd = [str(elem) for elem in cmd]

    if verbose:
        print(' '.join(cmd))

    p = subprocess.Popen(cmd)
    return p

if __name__ == '__main__':
    main()
