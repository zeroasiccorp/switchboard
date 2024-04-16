#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

"""
Basic reusable test for a memory chiplet
"""

import numpy as np
from util import (get_dtype_from_umi_size, dtype_random_data, umi_atomic_op)
from switchboard import (UmiTxRx, umi_pack, PyUmiPacket, UmiCmd, binary_run)


def memory_check(umi, device, test_rdma=False):
    print("### MINIMAL EXAMPLE ###")

    umi.write(0x1234, np.uint32(0xDEADBEEF))
    rdval = umi.read(0x1234, np.uint32)
    print(f"Read: {rdval}")
    assert rdval == 0xDEADBEEF

    umi.write(0x2345, np.arange(65, dtype=np.uint8))
    rdval = umi.read(0x2345, 65)
    print(f"Read: {rdval}")
    assert (rdval == np.arange(65, dtype=np.uint8)).all()

    umi.write(0x0, np.uint8(12))
    val1 = umi.atomic(0x0, np.uint8(23), 'add')
    val2 = umi.read(0x0, np.uint8)
    print(f"Atom: {val1}, Read: {val2}")
    assert val1 == 12
    assert val2 == 12 + 23

    if test_rdma:
        # write some data to a known location
        umi.write(0x3450, np.uint8([0xa, 0xb, 0xc, 0xd]))

        # send an RDMA request
        rdma_req = PyUmiPacket(
            cmd=umi_pack(UmiCmd.UMI_REQ_RDMA, 0, 0, 3, 1, 1, 0, 0, 0),
            dstaddr=0x3450,
            srcaddr=0x4560
        )
        umi.send(rdma_req)
        print('Sent RDMA request.')

        # check the RDMA response (which will come back as a posted write)
        p = device.recv()
        print(f"Received: {p.data}")
        assert np.array_equal(p.data, [0xa, 0xb, 0xc, 0xd])

    print("### WRITES ###")

    # 1 byte
    wrbuf = np.array([0xBAADF00D], np.uint32).view(np.uint8)
    for i in range(4):
        umi.write(0x10 + i, wrbuf[i])

    # 2 bytes
    wrbuf = np.array([0xB0BACAFE], np.uint32).view(np.uint16)
    for i in range(2):
        umi.write(0x20 + 2 * i, wrbuf[i])

    # 4 bytes
    umi.write(0x30, np.uint32(0xDEADBEEF))

    # 8 bytes
    umi.write(0x40, np.uint64(0xBAADD00DCAFEFACE))

    # 64 bytes
    wrbuf = np.arange(64, dtype=np.uint8)
    umi.write(0x50, wrbuf)

    print("### READS ###")

    # 1 byte
    rdbuf = np.empty((4,), dtype=np.uint8)
    for i in range(4):
        rdbuf[i] = umi.read(0x10 + i, np.uint8)
    val32 = rdbuf.view(np.uint32)[0]
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xBAADF00D

    # 2 bytes
    rdbuf = np.empty((2,), dtype=np.uint16)
    for i in range(2):
        rdbuf[i] = umi.read(0x20 + 2 * i, np.uint16)
    val32 = rdbuf.view(np.uint32)[0]
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xB0BACAFE

    # 4 bytes
    val32 = umi.read(0x30, np.uint32)
    print(f"Read: 0x{val32:08x}")
    assert val32 == 0xDEADBEEF

    # 8 bytes
    val64 = umi.read(0x40, np.uint64)
    print(f"Read: 0x{val64:016x}")
    assert val64 == 0xBAADD00DCAFEFACE

    # 64 bytes
    rdbuf = umi.read(0x50, 64)
    print("Read: {" + ", ".join([f"0x{elem:02x}" for elem in rdbuf]) + "}")
    assert (rdbuf == np.arange(64, dtype=np.uint8)).all()

    print("### ATOMICS ###")

    for size in [0, 1, 2, 3]:
        for cmd in ['swap', 'add', 'and', 'or', 'xor', 'min', 'max', 'minu', 'maxu']:
            # get the datatype
            dtype = get_dtype_from_umi_size(size=size)

            # get operands
            x = dtype_random_data(dtype)
            y = dtype_random_data(dtype)

            # test operation
            run_atomic(umi=umi, prev=x, data=y, cmd=cmd, sram_base=0)


def run_atomic(umi, prev, data, cmd, sram_base):
    print(f"* Atomic {cmd.upper()}, dtype={prev.dtype}")

    # determine the expected result of the atomic operation
    try:
        expected = umi_atomic_op(prev=prev, data=data, cmd=cmd)
    except ValueError:
        assert False, f"Invalid atomic operation {cmd}"

    # set memory to a specific value
    umi.write(sram_base, prev)

    # read old value
    val1 = umi.read(sram_base, prev.dtype)
    print(f"Read: 0x{val1:x}")
    assert val1 == prev

    # apply atomic operation
    val2 = umi.atomic(sram_base, data, cmd)
    print(f"Atom: 0x{val2:x}")
    assert val2 == prev

    # read new value
    val3 = umi.read(sram_base, prev.dtype)
    print(f"Read: 0x{val3:x}")
    assert val3 == expected


if __name__ == '__main__':
    umi = UmiTxRx('mem-req-rx.q', 'mem-rep-tx.q', fresh=True)
    binary_run(bin='./umi_mem', args=None)
    memory_check(umi=umi, device=None, test_rdma=False)
