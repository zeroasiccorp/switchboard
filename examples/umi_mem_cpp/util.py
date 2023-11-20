# General utilities for running tests.

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
import contextlib


@contextlib.contextmanager
def numpy_overflow_warning_off():
    """Context manager that temporarily disables the numpy overflow warning."""

    over = np.geterr()['over']
    np.seterr(over='ignore')

    yield

    np.seterr(over=over)


def get_dtype_from_umi_size(size, signed=False):
    """
    Returns a numpy datatype for a given UMI size and signedness.
    For example, get_dtype_from_umi_size(0) returns np.uint8, while
    get_dtype_from_umi_size(1, True) returns np.int16.
    """

    # make sure that the provided size is valid.
    assert size in {0, 1, 2, 3}, 'Only UMI sizes between 0 and 3 (inclusive) are allowed.'

    # determine the name of the datatype
    name = f"{'u' if not signed else 'i'}{1<<size}"

    # return the dtype
    return np.dtype(name)


def dtype_random_data(dtype, min_val=None, max_val=None):
    """Returns random data for the given data type between its minimum
    and maximum bounds.  The argument can be np.[u]int{8,16,32,64}"""

    if min_val is None:
        min_val = np.iinfo(dtype).min

    if max_val is None:
        max_val = np.iinfo(dtype).max

    return np.random.randint(min_val, max_val + 1, dtype=dtype)


def numpy_signed_view(value):
    """
    Returns a view of the given value as a signed integer.
    For example, numpy_signed_view(np.uint8(255)) should
    yield "-1" with a dtype of int8.
    """

    return value.view(np.dtype(f'i{value.itemsize}'))


def numpy_unsigned_view(value):
    """
    Returns a view of the given value as an unsigned integer.
    For example, numpy_unsigned_view(np.int8(-1)) should
    yield "255" with a dtype of uint8.
    """

    return value.view(np.dtype(f'u{value.itemsize}'))


def umi_atomic_op(prev, data, cmd):
    """
    Returns the expected result of a UMI atomic operation, i.e. the
    value expected to be read from memory immediately following an
    atomic operation.  "prev" is the previous value in memory, and
    "data" is the operand provided in the UMI packet.  "cmd" should
    be a member of the UmiCmd enum.
    """

    # make sure the data types are the same
    assert prev.dtype is data.dtype, ("Data types must be the same for both"
        " operands of an atomic operation.")

    if (cmd.upper() == 'SWAP'):
        return data
    elif (cmd.upper() == 'ADD'):
        # "add" may overflow, but that is not illegal per the UMI specification.
        # for example, the 8-bit operation 0xff + 0xff should yield 0xfe, not 0x1fe.
        # however, numpy will complain if overflow occurs, which adds noise to
        # the output of the test, so we need to temporarily disable the numpy warning.
        with numpy_overflow_warning_off():
            return (prev + data)
    elif (cmd.upper() == 'AND'):
        return (prev & data)
    elif (cmd.upper() == 'OR'):
        return (prev | data)
    elif (cmd.upper() == 'XOR'):
        return (prev ^ data)
    elif (cmd.upper() == 'MIN'):
        return min(numpy_signed_view(prev), numpy_signed_view(data)).view(prev.dtype)
    elif (cmd.upper() == 'MAX'):
        return max(numpy_signed_view(prev), numpy_signed_view(data)).view(prev.dtype)
    elif (cmd.upper() == 'MINU'):
        return min(numpy_unsigned_view(prev), numpy_unsigned_view(data)).view(prev.dtype)
    elif (cmd.upper() == 'MAXU'):
        return max(numpy_unsigned_view(prev), numpy_unsigned_view(data)).view(prev.dtype)
    else:
        raise ValueError("Invalid atomic operation.")
