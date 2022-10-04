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
    args = parser.parse_args()

    # clean up old queues if present
    for port in [5555, 5556]:
        filename = str(SHMEM_DIR / f'queue-{port}')
        try:
            os.remove(filename)
        except OSError:
            pass

    # start chip simulation
    start_chip()

    # wait for client to complete
    client = start_client()
    client.wait()

def start_chip():
    cmd = []
    cmd += ['vvp']
    cmd += ['-n']
    cmd += [f'-M{EXAMPLE_DIR / "icarus"}']
    cmd += ['-m', 'switchboard_vpi']
    cmd += [EXAMPLE_DIR / 'icarus' / 'testbench.vvp']
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
