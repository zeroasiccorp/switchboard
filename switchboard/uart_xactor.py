#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

"""
UMI/UART Transactor.
"""

import numpy as np


class uart_xactor:
    REG_TX = 0
    REG_RX = 4
    REG_SR = 8

    REGF_SR_RXEMPTY_MASK = 1 << 0
    REGF_SR_RXFULL_MASK = 1 << 1
    REGF_SR_TXEMPTY_MASK = 1 << 8
    REGF_SR_TXFULL_MASK = 1 << 9

    def __init__(self, umi, encoding='ascii'):
        self.encoding = encoding
        self.umi = umi

    def read_byte(self):
        c8 = None
        while True:
            sr = self.umi.read(self.REG_SR, np.uint32)
            if (sr & self.REGF_SR_RXEMPTY_MASK) == 0:
                rx = self.umi.read(self.REG_RX, np.uint32)
                c8 = rx & 0xff
                break
        return bytes([c8])

    def readline(self, size=-1, end='\n'):
        line = ""

        while size < 0 or len(line) < size:
            c8 = self.read_byte()
            if c8 == end.encode(self.encoding):
                break
            line += c8.decode(self.encoding)
        return line

    def write_byte(self, b):
        while True:
            sr = self.umi.read(self.REG_SR, np.uint32)
            if (sr & self.REGF_SR_TXFULL_MASK) == 0:
                self.umi.write(self.REG_TX, np.uint32(b))
                break

    # File-like ops
    def write(self, string):
        for b in string:
            self.write_byte(b)

    # On streaming UART, reading until EOF doesn't make sense
    # So we default the size arg to 1
    def read(self, size=1):
        data = bytes(0)
        while size < 0 or len(data) < size:
            b = self.read_byte()
            data += b
        return data
