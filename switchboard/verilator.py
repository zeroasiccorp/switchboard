# Utilities for working with Verilator
# Copyright (C) 2023 Zero ASIC

# TODO: replace with SiliconCompiler functionality

from .util import binary_run


def verilator_run(bin, plusargs=None, stop_timeout=10):
    args = []

    if plusargs is not None:
        assert isinstance(plusargs, list), 'plusargs must be a list'
        for plusarg in plusargs:
            if isinstance(plusarg, (list, tuple)):
                assert len(plusarg) == 2, 'only lists/tuples of length 2 allowed'
                args += [f'+{plusarg[0]}+{plusarg[1]}']
            else:
                args += [f'+{plusarg}']

    return binary_run(bin=bin, args=args, stop_timeout=stop_timeout, use_sigint=True)
