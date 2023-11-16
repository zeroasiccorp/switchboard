#!/usr/bin/env python3

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import os
import atexit
import subprocess
import argparse
import itertools

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
TOP_DIR = THIS_DIR.parent
SHMEM_DIR = THIS_DIR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--test', type=str, default='hello')
    parser.add_argument('--iterations', type=int, default=None)
    args = parser.parse_args()

    # set defaults
    if args.iterations is None:
        if args.test == 'bandwidth':
            args.iterations = 50000000
        elif args.test == 'latency':
            args.iterations = 5000000

    # provide unique queue numbers
    queue_counter = itertools.count(start=5555)

    # rx queue numbers
    rx = [None, None]

    if args.test in {'hello', 'bandwidth'}:
        rx[1] = next(queue_counter)
    elif args.test in {'latency'}:
        rx[0] = next(queue_counter)
        rx[1] = next(queue_counter)
    else:
        raise Exception(f'Unknown test: {args.test}')

    # split ports
    tx = [None, None]
    tx[0] = rx[1]
    tx[1] = rx[0]

    # clean up old queues if present
    for port in set(rx + tx):
        if port is not None:
            filename = str(SHMEM_DIR / f'queue-{port}')
            try:
                os.remove(filename)
            except OSError:
                pass

    # run the specific test of interest
    if args.test == 'hello':
        hello = THIS_DIR / 'hello.out'
        p = run_cmd(hello, 'rx', rx[1], auto_exit=False, verbose=args.verbose)
        run_cmd(hello, 'tx', tx[0], verbose=args.verbose)
        p.wait()
    elif args.test == 'bandwidth':
        bandwidth = THIS_DIR / 'bandwidth.out'
        p = run_cmd(bandwidth, 'rx', rx[1], args.iterations, auto_exit=False, verbose=args.verbose)
        run_cmd(bandwidth, 'tx', tx[0], args.iterations, verbose=args.verbose)
        p.wait()
    elif args.test == 'latency':
        latency = THIS_DIR / 'latency.out'
        run_cmd(latency, 'second', rx[0], tx[0], args.iterations, verbose=args.verbose)
        p = run_cmd(latency, 'first', rx[1], tx[1], args.iterations,
            auto_exit=False, verbose=args.verbose)
        p.wait()
    else:
        raise Exception(f'Unknown test: {args.test}')


def run_cmd(path, *args, auto_exit=True, verbose=False):
    cmd = []
    cmd += [path]
    cmd += args
    cmd = [str(elem) for elem in cmd]

    if verbose:
        print(' '.join(cmd))

    p = subprocess.Popen(cmd)

    if auto_exit:
        atexit.register(p.terminate)

    return p


if __name__ == '__main__':
    main()
