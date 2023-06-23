#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import numpy as np
from switchboard import UmiTxRx, delete_queue, verilator_run


def main(tx="queue-5555", rx="queue-5556"):
    # clean up old queues if present
    for q in [tx, rx]:
        delete_queue(q)

    # launch the simulation
    verilator_run('obj_dir/Vtestbench', plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi = UmiTxRx(tx, rx)

    print("### MINIMAL EXAMPLE ###")

    umi.write(0x0, np.uint32(0xDEADBEEF))
    rdval = umi.read(0x0, np.uint32)
    print(f"Read: 0x{rdval:08x}")
    assert rdval == 0xDEADBEEF

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


if __name__ == '__main__':
    main()
