# Utilities for working with Icarus Verilog

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

# TODO: replace with SiliconCompiler functionality

from typing import Union, List
from pathlib import Path

from .util import plusargs_to_args, binary_run
from .switchboard import path as sb_path
from subprocess import check_output, STDOUT, CalledProcessError


def run(command: list, cwd: str = None) -> str:
    return check_output(command, cwd=cwd, stderr=STDOUT).decode()


def icarus_build_vpi(
    cwd: str = None,
    name: str = 'switchboard',
    cincludes: List[str] = None,
    ldflags: List[str] = None
) -> str:
    if cincludes is None:
        cincludes = []

    if ldflags is None:
        ldflags = []

    sbdir = sb_path()
    incdirs = cincludes + [f'{sbdir}/cpp']

    cmd = []
    cmd += ['iverilog-vpi']
    cmd += [f'-I{incdir}' for incdir in incdirs]
    cmd += ldflags
    cmd += [str(sbdir / 'vpi' / f'{name}_vpi.cc')]

    try:
        run(cmd, cwd)
    except CalledProcessError as e:
        print(e.output)
        raise


def icarus_find_vpi(cwd: Union[str, Path] = None, name: str = 'switchboard') -> Path:
    path = Path(f'{name}_vpi.vpi')

    if cwd is not None:
        path = Path(cwd) / path

    if path.exists():
        return path
    else:
        return None


def icarus_run(vvp, plusargs=None, modules=None, extra_args=None, **kwargs):
    args = []

    args += ['-n']

    mdirs = set()

    if modules is not None:
        if not isinstance(modules, list):
            raise TypeError('modules must be a list')
        for module in modules:
            mdirs.add(str(Path(module.resolve().parent)))
            args += ['-m', Path(module).stem]

    for mdir in mdirs:
        args += [f'-M{mdir}']

    args += [vvp]
    args += plusargs_to_args(plusargs)

    if extra_args is not None:
        if not isinstance(modules, list):
            raise TypeError('extra_args must be a list')
        args += extra_args

    return binary_run(bin='vvp', args=args, **kwargs)
