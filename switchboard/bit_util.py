# Utilities for working with bit vectors using Verilog-style syntax, i.e. [MSB:LSB]

# Copyright (C) 2023 Zero ASIC

import numpy as np


class BitVector:
    def __init__(self, value: int = 0, bits: int = 32):
        if not isinstance(bits, int):
            raise ValueError('Number of bits must be provided as an integer.')

        if bits <= 0:
            raise ValueError('Number of bits must be positive.')

        self.bits = bits

        if 1 <= bits <= 8:
            self.dtype = np.uint8
        elif 9 <= bits <= 16:
            self.dtype = np.uint16
        elif 17 <= bits <= 32:
            self.dtype = np.uint32
        elif 33 <= bits <= 64:
            self.dtype = np.uint64
        else:
            raise ValueError(f'Number of bits is too large: {bits}')

        self.value = self.dtype(value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        nibbles = 2 * self.value.dtype.itemsize
        return f'0x{self.value:0{nibbles}x}'

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            msb, lsb = self.slice_to_msb_lsb(key.start, key.stop, key.step)
        else:
            msb, lsb = self.slice_to_msb_lsb(key, key)

        # generate mask with the right width
        mask = self.dtype((1 << (msb - lsb + 1)) - 1)

        # clear bit field using the mask
        new_value = self.value & (~(mask << self.dtype(lsb)))

        # set bit field
        new_value |= (self.dtype(value) & mask) << self.dtype(lsb)

        # set the new value (done here instead of through
        # incremental updates, to prevent the value from
        # being partially updated in case of an exception
        self.value = new_value

    def __getitem__(self, key):
        if isinstance(key, slice):
            msb, lsb = self.slice_to_msb_lsb(key.start, key.stop, key.step)
        else:
            msb, lsb = self.slice_to_msb_lsb(key, key)

        # generate mask with the right width
        mask = self.dtype((1 << (msb - lsb + 1)) - 1)

        # extract the value
        return (self.dtype(self.value) >> self.dtype(lsb)) & mask

    def slice_to_msb_lsb(self, start=None, stop=None, step=None):
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

        if msb >= self.bits:
            raise ValueError(f'MSB must be less than {self.bits}')

        return msb, lsb
