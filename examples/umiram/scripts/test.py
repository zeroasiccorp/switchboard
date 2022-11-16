#!/usr/bin/env python3

import os
import platform
import atexit
import subprocess
import argparse

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = THIS_DIR.parent
SHMEM_DIR = EXAMPLE_DIR

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    # clean up old queues if present
    for port in [5555, 5556, 5557]:
        filename = str(SHMEM_DIR / f'queue-{port}')
        try:
            os.remove(filename)
        except OSError:
            pass

    chip = start_chip()

    client = start_client()
    client.wait()

    chip.wait()

def start_chip(trace=True):
    cmd = []
    cmd += [EXAMPLE_DIR / 'verilator' / 'obj_dir' / 'Vtestbench']
    if trace:
        cmd += ['+trace']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)

    return p

def start_client():
    cmd = []
    cmd += [EXAMPLE_DIR / 'cpp' / 'client']
    cmd = [str(elem) for elem in cmd]

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)

    return p

if __name__ == '__main__':
    main()
