# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from .bitvector import BitVector


class UmiGpioInput:
    def __init__(self, width, dstaddr, srcaddr, max_bytes, umi):
        self.width = width
        self.dstaddr = dstaddr
        self.srcaddr = srcaddr
        self.max_bytes = max_bytes
        self.umi = umi

    def _read(self):
        # determine the number of bytes to read
        nbytes = (self.width // 8)
        if (self.width % 8) != 0:
            nbytes += 1

        # read the bytes
        return BitVector.frombytes(
            self.umi.read(
                addr=self.dstaddr,
                num_or_dtype=nbytes,
                dtype=np.uint8,
                srcaddr=self.srcaddr,
                max_bytes=self.max_bytes
            )
        )

    def __str__(self):
        return str(self._read())

    def __int__(self):
        return int(self[:])

    def __getitem__(self, key):
        bv = self._read()
        return bv.__getitem__(key=key)


class UmiGpioOutput:
    def __init__(self, width, init, dstaddr, srcaddr, posted, max_bytes, umi):
        self.width = width
        self.dstaddr = dstaddr
        self.srcaddr = srcaddr
        self.posted = posted
        self.max_bytes = max_bytes
        self.umi = umi

        self.bv = BitVector(init)

        if init is not None:
            self._write()

    def _write(self):
        # determine the number of bytes to write
        nbytes = (self.width // 8)
        if (self.width % 8) != 0:
            nbytes += 1

        # write the bytes
        self.umi.write(
            addr=self.dstaddr,
            data=self.bv.tobytes(n=nbytes),
            srcaddr=self.srcaddr,
            max_bytes=self.max_bytes,
            posted=self.posted
        )

    def __setitem__(self, key, value):
        self.bv.__setitem__(key=key, value=value)
        self._write()

    # read functions provided for convenience

    def __str__(self):
        return str(self.bv)

    def __int__(self):
        return int(self[:])

    def __getitem__(self, key):
        return self.bv.__getitem__(key=key)


class UmiGpio(object):
    def __init__(self, iwidth, owidth, init, dstaddr, srcaddr, posted, max_bytes, umi):

        self.i = UmiGpioInput(
            width=iwidth,
            dstaddr=dstaddr,
            srcaddr=srcaddr,
            max_bytes=max_bytes,
            umi=umi
        )

        self.o = UmiGpioOutput(
            width=owidth,
            init=init,
            dstaddr=dstaddr,
            srcaddr=srcaddr,
            posted=posted,
            max_bytes=max_bytes,
            umi=umi
        )
