#!/usr/bin/env python3

# Simple example illustrating switchboard bridging over TCP.
# Copyright (C) 2023 Zero ASIC

import sys
import numpy as np
from switchboard import delete_queue, PySbPacket, PySbTx, PySbRx, binary_run


def main(rxq='rx.q', txq='tx.q'):
    # clean up old queues if present
    for q in [rxq, txq]:
        delete_queue(q)

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    tx = PySbTx(rxq)
    rx = PySbRx(txq)

    # start TCP bridges
    start_tcp_bridge(mode='server', rx=rxq)
    start_tcp_bridge(mode='client', tx=txq)

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

    success = (rxp.data == txp.data).all()

    # declare test as having passed for regression testing purposes

    if success:
        print("PASS!")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


def start_tcp_bridge(mode, tx=None, rx=None, host=None, port=None, quiet=True):
    args = []
    args += ['--mode', mode]
    if tx is not None:
        args += ['--tx', tx]
    if rx is not None:
        args += ['--rx', rx]
    if host is not None:
        args += ['--host', host]
    if port is not None:
        args += ['--port', port]
    if quiet:
        args += ['-q']

    return binary_run(bin='sbtcp', args=args)


if __name__ == '__main__':
    main()
