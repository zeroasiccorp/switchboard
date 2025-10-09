# Utilities for working with Verilator

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

# TODO: replace with SiliconCompiler functionality

from .util import plusargs_to_args, binary_run


def verilator_run(bin, plusargs=None, args=None, use_sigint=True, **kwargs):
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
    args += plusargs_to_args(plusargs)

    # append any extra arguments user provided by the user
    args += extra_args

    return binary_run(bin=bin, args=args, use_sigint=use_sigint, **kwargs)
