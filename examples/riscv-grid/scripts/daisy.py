#!/usr/bin/env python

import time
import atexit
import subprocess
import argparse

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent

def main(start_port=5555, n_chips=10):
    parser = argparse.ArgumentParser()
    parser.add_argument('--sim', default='verilator')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    # chips
    for k in range(n_chips):
        p = start_chip(
            rx_port=start_port+k,
            tx_port=start_port+k+1,
            sim=args.sim,
            verbose=args.verbose
        )
        atexit.register(p.terminate)

    # client
    client = start_client(
        tx_port=start_port,
        rx_port=start_port+n_chips,
        bin = EXAMPLE_DIR / 'riscv' / 'daisy.bin',
        verbose=args.verbose
    )

    # wait for client to complete
    client.wait()

def start_chip(rx_port, tx_port, sim='verilator', verbose=False):
    cmd = []
    if sim == 'verilator':
        cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    else:
        raise Exception(f'Unknown simulator: {sim}')
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

    return p

def start_client(rx_port, tx_port, bin, verbose=False):
    cmd = []
    cmd += [EXAMPLE_DIR / 'cpp' / 'client']
    cmd += [rx_port]
    cmd += [tx_port]
    cmd += [bin]
    cmd = [str(elem) for elem in cmd]

    if verbose:
        print(' '.join(cmd))

    p = subprocess.Popen(cmd)
    return p

if __name__ == '__main__':
    main()
