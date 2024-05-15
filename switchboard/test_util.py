# General utilities for working with switchboard

# Copyright (c) 2024 Zero ASIC Corporation
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

    process = subprocess.Popen(args, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, bufsize=1, text=True, cwd=cwd)

    # print output while saving it
    stdout = ''
    for line in process.stdout:
        print(line, end='')
        stdout += line

    # make sure that process exits cleanly
    returncode = process.wait()
    assert returncode == 0, f'Exited with non-zero code: {returncode}'

    # check the results
    if expected is not None:
        if isinstance(expected, str):
            expected = [expected]
        for elem in expected:
            assert elem in stdout
