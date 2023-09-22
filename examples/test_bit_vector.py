#!/usr/bin/env python

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


if __name__ == '__main__':
    test_bit_vector()
