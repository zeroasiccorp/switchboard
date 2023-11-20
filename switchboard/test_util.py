# General utilities for working with switchboard

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import subprocess
from pathlib import Path


def test_cmd(args, expected=None, path=None):
    # determine where the command should be run
    if path is not None:
        path = Path(path)
        if path.is_file():
            cwd = path.resolve().parent
        elif path.is_dir():
            cwd = path.resolve()
        else:
            raise ValueError(f"Provided path doesn't exist: {path}")
    else:
        cwd = None

    # run the command, capturing the output
    if isinstance(args, str):
        args = [args]
    args = [str(arg) for arg in args]
    result = subprocess.run(args, check=True, capture_output=True,
        text=True, cwd=cwd)

    # print the output

    stdout = result.stdout
    if (stdout is not None) and (stdout != ''):
        print(stdout, end='', flush=True)

    stderr = result.stderr
    if (stderr is not None) and (stderr != ''):
        print('### STDERR ###')
        print(stderr, end='', flush=True)

    # check the results
    if expected is not None:
        if isinstance(expected, str):
            expected = [expected]
        for elem in expected:
            assert elem in stdout
