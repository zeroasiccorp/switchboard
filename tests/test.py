#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import time
import atexit
import argparse
import itertools

from pathlib import Path
from switchboard import binary_run, delete_queue, start_tcp_bridge

THIS_DIR = Path(__file__).resolve().parent
TOP_DIR = THIS_DIR.parent

QUEUE_COUNTER = itertools.count(start=0)


def next_queue():
    queue = str(THIS_DIR / f'queue-{next(QUEUE_COUNTER)}')
    delete_queue(queue)
    atexit.register(lambda queue=queue: delete_queue(queue))
    return queue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--test', type=str, default='hello',
        choices=['hello', 'bandwidth', 'latency'])
    parser.add_argument('--iterations', type=int, default=None)
    parser.add_argument('--tcp', action='store_true')
    args = parser.parse_args()

    # set defaults
    if args.iterations is None:
        if args.test == 'bandwidth':
            args.iterations = 50000000 if not args.tcp else 40000
        elif args.test == 'latency':
            args.iterations = 5000000 if not args.tcp else 5000

    # determine the number of paths
    if args.test in {'hello', 'bandwidth'}:
        num_paths = 1
    elif args.test in {'latency'}:
        num_paths = 2
    else:
        raise Exception(f'Unknown test: {args.test}')

    # create the paths
    paths = []
    port = 5555
    for _ in range(num_paths):
        a = next_queue()

        if args.tcp:
            b = next_queue()

            print(f'Starting TCP bridge at port {port}... ', end='', flush=True)

            start_tcp_bridge(inputs=[a], port=port)
            start_tcp_bridge(outputs=[('*', b)], port=port)

            time.sleep(2)
            print('done')

            port += 1
        else:
            b = a

        paths.append((a, b))

    # run the specific test of interest
    if args.test == 'hello':
        hello = THIS_DIR / 'hello.out'
        p = binary_run(hello, ['rx', paths[0][1]])
        binary_run(hello, ['tx', paths[0][0]])
        exit(p.wait())
    elif args.test == 'bandwidth':
        bandwidth = THIS_DIR / 'bandwidth.out'
        p = binary_run(bandwidth, ['rx', paths[0][1], args.iterations])
        binary_run(bandwidth, ['tx', paths[0][0], args.iterations])
        exit(p.wait())
    elif args.test == 'latency':
        latency = THIS_DIR / 'latency.out'
        binary_run(latency, ['second', paths[0][1], paths[1][0], args.iterations])
        p = binary_run(latency, ['first', paths[1][1], paths[0][0], args.iterations])
        exit(p.wait())
    else:
        raise Exception(f'Unknown test: {args.test}')


if __name__ == '__main__':
    main()
