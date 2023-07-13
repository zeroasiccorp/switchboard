# Utilities for working with the old-to-new UMI converter program
# Copyright (C) 2023 Zero ASIC

import subprocess
from pathlib import Path
from .util import binary_run

THIS_DIR = Path(__file__).resolve().parent
OLD2NEW = THIS_DIR / 'cpp' / 'old2new'


def old2new_build(bin=None):
    if bin is None:
        bin = OLD2NEW

    result = subprocess.run(['make', bin.name], cwd=bin.parent)
    assert result.returncode == 0


def none_to_empty_str(x):
    if x is None:
        return ''
    else:
        return x


def old2new_run(connections=None, verbose=False, should_yield=False, bin=None,
    old_rx=None, old_tx=None, new_req_rx=None, new_req_tx=None,
    new_resp_rx=None, new_resp_tx=None):

    # set defaults

    if connections is None:
        connections = []
    elif not isinstance(connections, (list, tuple)):
        connections = [connections]

    if any(x is not None for x in
        [old_rx, old_tx, new_req_rx, new_req_tx, new_resp_rx, new_resp_tx]):
        connections.append(dict(old_rx=old_rx, old_tx=old_tx, new_req_rx=new_req_rx,
            new_req_tx=new_req_tx, new_resp_rx=new_resp_rx, new_resp_tx=new_resp_tx))

    if bin is None:
        bin = OLD2NEW

    # build old2new if needed

    if not bin.exists():
        old2new_build(bin)

    # run the program

    args = []

    for conn in connections:
        old_rx = none_to_empty_str(conn.get('old_rx', ''))
        old_tx = none_to_empty_str(conn.get('old_tx', ''))
        new_req_rx = none_to_empty_str(conn.get('new_req_rx', ''))
        new_req_tx = none_to_empty_str(conn.get('new_req_tx', ''))
        new_resp_rx = none_to_empty_str(conn.get('new_resp_rx', ''))
        new_resp_tx = none_to_empty_str(conn.get('new_resp_tx', ''))

        # trailing colon is important
        args.append(f'{old_rx}:{old_tx}:{new_req_rx}:{new_req_tx}:{new_resp_rx}:{new_resp_tx}:')

    if verbose:
        args.append('-v')

    if should_yield:
        args.append('--should-yield')

    return binary_run(bin=bin, args=args)
