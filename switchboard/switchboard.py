# Switchboard CLI
# Copyright (C) 2023 Zero ASIC

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
