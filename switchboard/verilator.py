# Utilities for working with Verilator
# Copyright (C) 2023 Zero ASIC

# TODO: replace with SiliconCompiler functionality

from .util import binary_run


def verilator_run(bin, plusargs=None, args=None, **kwargs):
    if args is None:
        extra_args = []
    elif isinstance(args, (list, tuple)):
        # even if args is already a list, make a copy to
        # ensure that changes don't propagate back to the
        # value that the user provided for args
        extra_args = list(args)
    else:
        # if the user provided a single value for args,
        # wrap it in a list rather than erroring out
        extra_args = [args]

    # build up the argument list
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

    # append any extra arguments user provided by the user
    args += extra_args

    return binary_run(bin=bin, args=args, **kwargs)
