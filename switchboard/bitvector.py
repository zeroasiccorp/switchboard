# Utilities for working with bit vectors using Verilog-style syntax, i.e. [MSB:LSB]

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np


class BitVector:
    def __init__(self, value: int = 0):
        self.value = int(value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return f'0x{self.value:x}'

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if (key.start is None) and (key.stop is None) and (key.step is None):
                self.value = value
                return
            else:
                msb, lsb = slice_to_msb_lsb(key.start, key.stop, key.step)
        else:
            msb, lsb = slice_to_msb_lsb(key, key)

        # generate mask with the right width
        mask = (1 << (msb - lsb + 1)) - 1

        # clear bit field using the mask
        new_value = self.value & (~(mask << lsb))

        # set bit field
        new_value |= (value & mask) << lsb

        # set the new value (done here instead of through
        # incremental updates, to prevent the value from
        # being partially updated in case of an exception
        self.value = new_value

    def __getitem__(self, key):
        if isinstance(key, slice):
            if (key.start is None) and (key.stop is None) and (key.step is None):
                return self.value
            else:
                msb, lsb = slice_to_msb_lsb(key.start, key.stop, key.step)
        else:
            msb, lsb = slice_to_msb_lsb(key, key)

        # generate mask with the right width
        mask = (1 << (msb - lsb + 1)) - 1

        # extract the value
        return (self.value >> lsb) & mask

    def tobytes(self, n=None):
        # convert to a numpy byte array.  if "n" is provided,
        # pad result to be "n" bytes.  will error out if "n"
        # is less than the number of bytes needed to represent
        # the current value.

        value = self.value
        bytes = []

        while value != 0:
            bytes.append(value & 0xff)
            value >>= 8

        if n is not None:
            if len(bytes) < n:
                bytes += [0] * (n - len(bytes))
            elif len(bytes) > n:
                raise ValueError('Number of bytes needed to represent the current value'
                    f' ({self.value}) is {len(bytes)}, but the argument n={n} is smaller.')

        return np.array(bytes, dtype=np.uint8)

    @staticmethod
    def frombytes(arr):
        value = 0

        for i, elem in enumerate(arr):
            if not (0 <= elem <= 255):
                raise ValueError(f'Non-byte value detected at index {i}: {elem}')
            value |= (int(elem) & 0xff) << (i * 8)

        return BitVector(value)


def slice_to_msb_lsb(start=None, stop=None, step=None):
    # set defaults
    if start is None:
        start = 0
    if stop is None:
        stop = 0
    if step is None:
        step = 1

    if step != 1:
        raise ValueError('Only step=1 allowed for slice indexing.')

    msb = start
    lsb = stop

    if msb < lsb:
        raise ValueError('MSB must be greater than or equal to LSB')
    if lsb < 0:
        raise ValueError('Negative LSB is not allowed.')

    return msb, lsb
