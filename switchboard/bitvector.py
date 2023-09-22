# Utilities for working with bit vectors using Verilog-style syntax, i.e. [MSB:LSB]

# Copyright (C) 2023 Zero ASIC


class BitVector:
    def __init__(self, value: int = 0):
        self.value = int(value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return f'0x{self.value:x}'

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            msb, lsb = self.slice_to_msb_lsb(key.start, key.stop, key.step)
        else:
            msb, lsb = self.slice_to_msb_lsb(key, key)

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
            msb, lsb = self.slice_to_msb_lsb(key.start, key.stop, key.step)
        else:
            msb, lsb = self.slice_to_msb_lsb(key, key)

        # generate mask with the right width
        mask = (1 << (msb - lsb + 1)) - 1

        # extract the value
        return (self.value >> lsb) & mask

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

        return msb, lsb
