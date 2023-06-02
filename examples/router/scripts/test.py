#!/usr/bin/env python3

import os
import atexit
import subprocess

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent
TOP_DIR = EXAMPLE_DIR.parent.parent
SHMEM_DIR = EXAMPLE_DIR


def main():
    # clean up old queues if present
    for port in [5555, 5556, 5557, 5558]:
        filename = str(SHMEM_DIR / f'queue-{port}')
        try:
            os.remove(filename)
        except OSError:
            pass

    # start chip simulation
    start_chip()

    # start router
    start_router()

    # wait for client to complete
    client = start_client()
    client.wait()


def start_chip():
    cmd = []
    cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)


def start_router():
    cmd = []
    cmd += [TOP_DIR / 'cpp' / 'router']
    cmd += ['--tx', 5556, 5557]
    cmd += ['--rx', 5555, 5558]
    cmd += ['--route', '0:5556', '1:5557']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)


def start_client():
    cmd = []
    cmd += [EXAMPLE_DIR / 'cpp' / 'client']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)
    return p


if __name__ == '__main__':
    main()
