#!/usr/bin/env python3

# Simple example illustrating the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import sys
import numpy as np
from switchboard import delete_queue, PySbPacket, PySbTx, PySbRx, verilator_run


def main(client2rtl='client2rtl.q', rtl2client='rtl2client.q'):
    # clean up old queues if present
    for q in [client2rtl, rtl2client]:
        delete_queue(q)

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    tx = PySbTx(client2rtl)
    rx = PySbRx(rtl2client)

    # start chip simulation
    chip = verilator_run('obj_dir/Vtestbench', plusargs=['trace'])

    # form packet to be sent into the simulation.  note that the arguments
    # to the constructor are all optional, and can all be specified later
    txp = PySbPacket(
        destination=123456789,
        flags=1,
        data=np.array([(i & 0xff) for i in range(32)], dtype=np.uint8)
    )

    # send the packet

    tx.send(txp)  # note: blocking by default, can disable with blocking=False
    print("*** TX packet ***")
    print(txp)
    print()

    # receive packet

    rxp = rx.recv()  # note: blocking by default, can disable with blocking=False
    rxp.data = rxp.data[:32]

    print("*** RX packet ***")
    print(rxp)
    print()

    # check that the received data

    success = (rxp.data == (txp.data + 1)).all()

    # stop simulation

    tx.send(PySbPacket(data=np.array([0xff for _ in range(32)], dtype=np.uint8)))
    chip.wait()

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == '__main__':
    main()
