# Utilities for working with Icarus Verilog
# Copyright (C) 2023 Zero ASIC

# TODO: replace with SiliconCompiler functionality

from pathlib import Path

from .util import binary_run


def icarus_run(vvp, modules=None, extra_args=None, stop_timeout=10):
    args = []

    args += ['-n']

    if modules is not None:
        assert isinstance(modules, list), 'modules must be a list'
        for module in modules:
            args += [f'-M{Path(module.resolve().parent)}']
            args += ['-m', Path(module).stem]

    args += [vvp]

    if extra_args is not None:
        assert isinstance(modules, list), 'extra_args must be a list'
        args += extra_args

    return binary_run(bin='vvp', args=args, stop_timeout=stop_timeout, use_sigint=True)
