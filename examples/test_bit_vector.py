#!/usr/bin/env python

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from switchboard import BitVector


def test_bit_vector():
    bv = BitVector(0xdeadbeef)
    assert bv.value == 0xdeadbeef

    bv[31:16] = 0xcafe
    assert bv.value == 0xcafebeef

    bv[15:8] = 0xd0
    assert bv.value == 0xcafed0ef

    bv[7:0] = 0x0d
    assert bv.value == 0xcafed00d

    assert np.array_equal(bv.tobytes(), np.array([0x0d, 0xd0, 0xfe, 0xca], dtype=np.uint8))


if __name__ == '__main__':
    test_bit_vector()
