# Switchboard CLI

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import ArgumentParser
from pathlib import Path


def path():
    return Path(__file__).resolve().parent


def main():
    parser = ArgumentParser()
    parser.add_argument('--path', action='store_true')

    args = parser.parse_args()

    if args.path:
        print(path())
