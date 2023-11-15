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
    parser.add_argument('--mode', type=str, default='queue')
    parser.add_argument('--test', type=str, default='hello')
    parser.add_argument('--iterations', type=int, default=None)
    args = parser.parse_args()

    # set defaults
    if args.iterations is None:
        if args.test == 'bandwidth':
            args.iterations = 50000000
        elif args.test == 'latency':
            if args.mode == 'queue':
                args.iterations = 5000000
            elif args.mode == 'tcp':
                args.iterations = 50000
            else:
                raise Exception(f'Invalid mode: {args.mode}')

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

    # split ports based on communication mode
    tx = [None, None]
    if args.mode == 'queue':
        tx[0] = rx[1]
        tx[1] = rx[0]
    elif args.mode == 'tcp':
        if rx[1] is not None:
            tx[0] = next(queue_counter)
        if rx[0] is not None:
            tx[1] = next(queue_counter)
    else:
        raise Exception(f'Unknown mode: {args.mode}')

    # clean up old queues if present
    for port in set(rx + tx):
        if port is not None:
            filename = str(SHMEM_DIR / f'queue-{port}')
            try:
                os.remove(filename)
            except OSError:
                pass

    # start bridge programs if relevant
    if args.mode == 'tcp':
        # start server
        p = start_bridge(is_server=True, rx_port=tx[0], tx_port=rx[0], verbose=args.verbose)

        # start client
        start_bridge(is_server=False, rx_port=tx[1], tx_port=rx[1], verbose=args.verbose)

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


def start_bridge(is_server=False, rx_port=None, tx_port=None,
    tcp_addr='127.0.0.1', tcp_port=7777, verbose=False):

    # set defaults
    if rx_port is None:
        rx_port = -1
    if tx_port is None:
        tx_port = -1

    args = []
    args += ['-s' if is_server else '-c']
    args += [rx_port]
    args += [tx_port]
    args += [tcp_addr]
    args += [tcp_port]

    return run_cmd(TOP_DIR / 'cpp' / 'tcp-bridge', *args, auto_exit=True, verbose=verbose)


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
