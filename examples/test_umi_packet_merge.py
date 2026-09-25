#!/usr/bin/env python

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np
from switchboard import PyUmiPacket, UmiCmd, umi_pack, umi_len, umi_eom

# SIZE=0 means one byte per word, so LEN+1 is also the number of data bytes
SIZE = 0


def make_packet(len_field, dstaddr, srcaddr, eom=0):
    cmd = umi_pack(UmiCmd.UMI_REQ_WRITE, 0, SIZE, len_field, eom, 0)
    data = np.arange(len_field + 1, dtype=np.uint8)
    return PyUmiPacket(cmd, dstaddr, srcaddr, data)


def test_merge_within_len_limit():
    # 255 words + 1 word fills the LEN field exactly, so this merge is allowed
    p = make_packet(254, 0, 0)
    q = make_packet(0, 255, 255, eom=1)

    assert p.merge(q)

    assert umi_len(p.cmd) == 255
    assert umi_eom(p.cmd) == 1
    assert p.data.size == 256
    assert p.data[255] == q.data[0]


def test_merge_beyond_len_limit_rejected():
    # 255 words + 6 words needs a LEN of 260, which does not fit in the
    # eight-bit LEN field, so the merge must be refused rather than wrapping
    p = make_packet(254, 0, 0)
    q = make_packet(5, 255, 255, eom=1)

    cmd_before = p.cmd

    assert not p.merge(q)

    # the rejected merge must leave the packet untouched
    assert p.cmd == cmd_before
    assert umi_len(p.cmd) == 254
    assert umi_eom(p.cmd) == 0
    assert p.data.size == 255


def test_merge_ordinary_packets():
    p = make_packet(3, 0, 0)
    q = make_packet(1, 4, 4, eom=1)

    assert p.merge(q)

    assert umi_len(p.cmd) == 5
    assert umi_eom(p.cmd) == 1
    assert np.array_equal(p.data, np.array([0, 1, 2, 3, 0, 1], dtype=np.uint8))


if __name__ == '__main__':
    test_merge_within_len_limit()
    test_merge_beyond_len_limit_rejected()
    test_merge_ordinary_packets()
