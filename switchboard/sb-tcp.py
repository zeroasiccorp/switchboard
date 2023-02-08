#!/usr/bin/env python3

# Command-line tool that bridges Switchboard packets over TCP.

# Copyright (C) 2023 Zero ASIC

# TODO: make this generic for Switchboard connections
# using the "last" flag to indicate the boundaries
# of transactions.

# reference for setting up Python TCP connections:
# https://realpython.com/python-sockets/#echo-client-and-server

# reference for non-blocking socket programming:
# https://stackoverflow.com/a/16745561

import time
import errno
import socket
import argparse
import numpy as np
from switchboard import PySbRx, PySbTx, PySbPacket

SB_PACKET_SIZE_BYTES = 40

def main():
    # parse command-line arguments

    parser = get_parser()
    args = parser.parse_args()

    # initialize RX

    if args.rx != "":
        sbrx = PySbRx(args.rx)
        tcp_tx_alive = True
    else:
        sbrx = None
        tcp_tx_alive = False

    # initialize TX

    if args.tx != "":
        sbtx = PySbTx(args.tx)
        tcp_rx_alive = True
    else:
        sbtx = None
        tcp_rx_alive = False

    # initialize TCP

    if args.mode == 'server':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow port to be reused immediately
        s.bind((args.host, args.port))
        s.listen()
        if not args.q:
            print('Waiting for client...')
        conn, addr = s.accept()
    elif args.mode == 'client':
        if not args.q:
            print('Waiting for server', end='', flush=True)
        while True:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((args.host, args.port))
                break
            except ConnectionRefusedError:
                if not args.q:
                    print('.', end='', flush=True)
                time.sleep(1)
        if not args.q:                
            print()
    else:
        raise ValueError(f"Invalid mode: {args.mode}")
    if not args.q:
        print('Done.')

    # main loop

    while True:
        # receive data from SB queue and send it over TCP
        if (sbrx is not None) and tcp_tx_alive:
            p = sbrx.recv()
            if p is not None:
                data = sb2bytes(p)
                conn.setblocking(True)
                conn.sendall(data)

        # receive data from TCP and send it to a SB queue
        if (sbtx is not None) and tcp_rx_alive:
            # find out if there is any data to receive
            # must not block if the same connection is being
            # used in the other direction

            try:
                if (sbrx is not None) and tcp_tx_alive:
                    conn.setblocking(False)
                b = conn.recv(SB_PACKET_SIZE_BYTES)
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    pass
                else:
                    raise
            else:
                if len(b) == 0:
                    # done receiving data over TCP
                    tcp_rx_alive = False
                else:
                    # we have some data to send, so get the rest
                    conn.setblocking(True)
                    while len(b) < SB_PACKET_SIZE_BYTES:
                        b += conn.recv(SB_PACKET_SIZE_BYTES-len(b))
            
                    # send the packet to a Switchboard queue
                    sbtx.send(bytes2sb(b))

def sb2bytes(p):
    # construct a byte array from 
    arr = np.concatenate((
        np.array([p.destination, p.flags], dtype=np.uint32),
        p.data.view(np.uint32)
    ))
    return arr.tobytes()

def bytes2sb(b):
    arr = np.frombuffer(b, dtype=np.uint32)
    return PySbPacket(arr[0], arr[1], arr[2:].view(np.uint8))

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rx', type=str, default="")
    parser.add_argument('--tx', type=str, default="")
    parser.add_argument('--mode', type=str, required=True, choices=["server", "client"])
    parser.add_argument('--port', type=int, default=5555)
    parser.add_argument('--host', type=str, default="localhost")
    parser.add_argument('-q', action='store_true')
    return parser

if __name__ == "__main__":
    main()
