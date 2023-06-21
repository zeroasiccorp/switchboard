#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
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

    # write 0xbeefcafe to address 0x12

    wr_addr = 0x12
    wr_data = np.uint32(0xbeefcafe)
    umi.write(wr_addr, wr_data)
    print(f"Wrote to 0x{wr_addr:02x}: 0x{wr_data:08x}")

    # read data from address 0x12

    rd_addr = wr_addr
    rd_data = umi.read(rd_addr, np.uint32)
    print(f"Read from 0x{rd_addr:02x}: 0x{rd_data:08x}")

    # declare test as having passed for regression testing purposes

    if rd_data == wr_data:
        print('PASS!')
        sys.exit(0)
    else:
        print('FAIL')
        sys.exit(1)


if __name__ == '__main__':
    main()
