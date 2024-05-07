# Switchboard CLI

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from argparse import ArgumentParser
from pathlib import Path


def path():
    return Path(__file__).resolve().parent


def inspect(file, format):
    import shutil
    import tempfile

    with tempfile.NamedTemporaryFile() as temp:
        shutil.copyfile(file, temp.name)

        if format == 'sb':
            from switchboard import PySbRx
            rx = PySbRx(temp.name, fresh=False)
        elif format == 'umi':
            from switchboard import UmiTxRx
            rx = UmiTxRx(rx_uri=temp.name, fresh=False)
        else:
            raise ValueError(f'Format not supported: "{format}"')

        while True:
            rxp = rx.recv(False)

            if rxp is not None:
                print(rxp)
            else:
                break


def main():
    parser = ArgumentParser()
    parser.add_argument('--path', action='store_true')
    parser.add_argument('-i', '--inspect', type=str, default=None, help='Print the contents'
        ' of the given switchboard queue.')
    parser.add_argument('-f', '--format', type=str, default='sb', choices=['sb', 'umi'],
        help='Format assumed for the contents of the switchboard queue passed via the'
        ' -i/--inspect argument.')

    args = parser.parse_args()

    if args.path:
        print(path())
    elif args.inspect is not None:
        inspect(file=args.inspect, format=args.format)
