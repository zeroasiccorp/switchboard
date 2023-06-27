# Utilities for working with Verilator
# Copyright (C) 2023 Zero ASIC

# TODO: replace with SiliconCompiler functionality

from .util import binary_run


def verilator_run(bin, plusargs=None, **kwargs):
    args = []

    if plusargs is not None:
        if not isinstance(plusargs, list):
            raise TypeError('plusargs must be a list')
        for plusarg in plusargs:
            if isinstance(plusarg, (list, tuple)):
                if len(plusarg) != 2:
                    raise ValueError('Only lists/tuples of length 2 allowed')
                args += [f'+{plusarg[0]}={plusarg[1]}']
            else:
                args += [f'+{plusarg}']

    return binary_run(bin=bin, args=args, **kwargs)
