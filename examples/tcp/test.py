#!/usr/bin/env python3

# Example showing how to connect simulations over TCP

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
from switchboard import binary_run


def main():
    binary_run(sys.executable, ['ram.py', '--fast'], cwd='ram', use_sigint=True)

    fifos = binary_run(sys.executable, ['fifos.py', '--fast'], cwd='fifos')
    fifos.wait()

    print('PASS!')


if __name__ == '__main__':
    main()
