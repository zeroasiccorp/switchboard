# Utilities for working with Icarus Verilog

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

# TODO: replace with SiliconCompiler functionality

from typing import Union
from pathlib import Path

from .util import plusargs_to_args, binary_run
from .switchboard import path as sb_path
from subprocess import check_output, STDOUT


def run(command: list, cwd: str = None) -> str:
    return check_output(command, cwd=cwd, stderr=STDOUT).decode()


def icarus_build_vpi(cwd: str = None) -> str:
    sbdir = sb_path()
    vpi_cc = sbdir / 'vpi/switchboard_vpi.cc'
    vpi_flags = f'-I{sbdir}/cpp'
    return run(['iverilog-vpi', vpi_flags, vpi_cc], cwd)


def icarus_find_vpi(cwd: Union[str, Path] = None) -> Path:
    path = Path('switchboard_vpi.vpi')

    if cwd is not None:
        path = Path(cwd) / path

    if path.exists():
        return path
    else:
        return None


def icarus_run(vvp, plusargs=None, modules=None, extra_args=None, **kwargs):
    args = []

    args += ['-n']

    if modules is not None:
        if not isinstance(modules, list):
            raise TypeError('modules must be a list')
        for module in modules:
            args += [f'-M{Path(module.resolve().parent)}']
            args += ['-m', Path(module).stem]

    args += [vvp]
    args += plusargs_to_args(plusargs)

    if extra_args is not None:
        if not isinstance(modules, list):
            raise TypeError('extra_args must be a list')
        args += extra_args

    return binary_run(bin='vvp', args=args, **kwargs)
