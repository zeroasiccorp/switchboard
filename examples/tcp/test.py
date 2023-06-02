#!/usr/bin/env python3

# Simple example illustrating switchboard bridging over TCP.
# Copyright (C) 2023 Zero ASIC

import sys
import atexit
import subprocess
import numpy as np
from switchboard import delete_queue, PySbPacket, PySbTx, PySbRx


def main():
    # clean up old queues if present
    for q in ['queue-5555', 'queue-5556']:
        delete_queue(q)

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    tx = PySbTx("queue-5555")
    rx = PySbRx("queue-5556")

    # start TCP bridges
    start_tcp_bridge(mode='server', rx="queue-5555")
    start_tcp_bridge(mode='client', tx="queue-5556")

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
    cmd = []
    cmd += ['sbtcp']
    cmd += ['--mode', mode]
    if tx is not None:
        cmd += ['--tx', tx]
    if rx is not None:
        cmd += ['--rx', rx]
    if host is not None:
        cmd += ['--host', host]
    if port is not None:
        cmd += ['--port', port]
    if quiet:
        cmd += ['-q']
    cmd = [str(elem) for elem in cmd]
    print(cmd)

    p = subprocess.Popen(cmd)

    atexit.register(p.terminate)

    return p


if __name__ == '__main__':
    main()
