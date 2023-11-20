#!/usr/bin/env python3

# Command-line tool that bridges Switchboard packets over TCP.

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

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

SB_PACKET_SIZE_BYTES = 60


def conn_closed(conn):
    """
    Check if connection is closed by peeking into the read buffer.
    """
    try:
        buf = conn.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
        if len(buf) == 0:
            # Read of zero means connection was closed.
            return True
    except socket.error as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            # Some other error, re-raise since this was not expected.
            raise e

    # Connection seems to be alive.
    return False


def run_tcp_bridge(sbrx, sbtx, conn, should_yield=True):
    """
    Sends packets received from PySbRx "sbrx" to TCP connection "conn",
    and sends packets received from "conn" to PySbTx "sbtx".  Runs
    continuously until the connection breaks.

    The optional argument "should_yield" indicates if the bridge
    should yield when there is no activity, or when congestion is
    detected.  The default is that yielding does occur, so that
    the bridge doesn't use unnecessary CPU resources.  However,
    this will increase latency as compared to the case where
    there is no explicit yielding.
    """

    # set connection to non-blocking, allowing SB and TCP
    # send/recv operations to be fully interleaved
    conn.setblocking(False)

    # packets in progress of being sent/received
    tcp_data_to_send = bytes([])
    data_rx_from_tcp = bytes([])

    # continue bridging until the connection isn't alive anymore
    while True:
        #############
        # SB -> TCP #
        #############

        sb2tcp_votes_to_yield = False

        if sbrx is not None:
            # get a new packet if needed
            if tcp_data_to_send == bytes([]):
                p = sbrx.recv(blocking=False)
                if p is not None:
                    # convert the packet to a bytes object
                    tcp_data_to_send = sb2bytes(p)
                else:
                    # no data to pass on to TCP, so indicate
                    # that we may want to yield to other threads
                    sb2tcp_votes_to_yield = True

            # if there is a new packet to send along try to send a chunk of it
            # in a non-blocking fashion
            if tcp_data_to_send != bytes([]):
                try:
                    n = conn.send(tcp_data_to_send)
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        # couldn't send anything over TCP, so indicate
                        # that we may want to yield to other threads
                        sb2tcp_votes_to_yield = True
                    else:
                        raise
                else:
                    if n == 0:
                        # connection is not alive anymore
                        break
                    else:
                        tcp_data_to_send = tcp_data_to_send[n:]
            if conn_closed(conn):
                break
        else:
            # there is no channel for receiving SB packets
            sb2tcp_votes_to_yield = True

        #############
        # TCP -> SB #
        #############

        tcp2sb_votes_to_yield = False

        # receive data from TCP and send it to a SB queue
        if sbtx is not None:
            # receive more data from TCP if needed
            if len(data_rx_from_tcp) != SB_PACKET_SIZE_BYTES:
                try:
                    b = conn.recv(SB_PACKET_SIZE_BYTES)
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        # couldn't receive anything over TCP, so indicate
                        # that we may want to yield to other threads
                        tcp2sb_votes_to_yield = True
                    else:
                        raise
                else:
                    if len(b) == 0:
                        # connection is not alive anymore
                        break
                    else:
                        data_rx_from_tcp += b

            # try to send a Switchboard packet to a queue if we have one to send
            if len(data_rx_from_tcp) == SB_PACKET_SIZE_BYTES:
                if sbtx.send(bytes2sb(data_rx_from_tcp), blocking=False):
                    data_rx_from_tcp = bytes([])
                else:
                    # couldn't send a packet to a Switchboard queue, so indicate
                    # that we may want to yield to other threads
                    tcp2sb_votes_to_yield = True
        else:
            # there is no channel for transmitting SB packets
            tcp2sb_votes_to_yield = True

        ############
        # yielding #
        ############

        # yield if nothing is happening or it looks like we're blocked
        # due to backpressure

        if sb2tcp_votes_to_yield and tcp2sb_votes_to_yield and should_yield:
            time.sleep(0)


def run_client(sbrx, sbtx, host, port, quiet=False, should_yield=True):
    """
    Connect to a server, retrying until a connection is made.
    """

    # initialize TX/RX if needed
    sbrx = convert_to_queue(sbrx, 'sbrx', PySbRx)
    sbtx = convert_to_queue(sbtx, 'sbtx', PySbTx)

    if not quiet:
        print('Waiting for server', end='', flush=True)
    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((host, port))
            break
        except ConnectionRefusedError:
            if not quiet:
                print('.', end='', flush=True)
            time.sleep(1)
    if not quiet:
        print()
        print('Done.')

    # communicate with the server
    run_tcp_bridge(sbrx=sbrx, sbtx=sbtx, conn=conn, should_yield=should_yield)


def run_server(sbrx, sbtx, host, port, quiet=False, should_yield=True, run_once=False):
    """
    Accepts client connections in a loop until Ctrl-C is pressed.
    """

    # initialize TX/RX if needed
    sbrx = convert_to_queue(sbrx, 'sbrx', PySbRx)
    sbtx = convert_to_queue(sbtx, 'sbtx', PySbTx)

    # create the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET,
        socket.SO_REUSEADDR, 1)  # allow port to be reused immediately
    server_socket.bind((host, port))
    server_socket.listen()

    # accept client connections in a loop
    while True:
        # accept a client
        if not quiet:
            print('Waiting for client...')
        conn, _ = server_socket.accept()
        if not quiet:
            print('Done.')

        # communicate with that client
        run_tcp_bridge(sbrx=sbrx, sbtx=sbtx, conn=conn, should_yield=should_yield)
        if (run_once):
            break


def main():
    # parse command-line arguments

    parser = get_parser()
    args = parser.parse_args()

    # main logic

    if args.mode == 'server':
        run_server(sbrx=args.rx, sbtx=args.tx, host=args.host, port=args.port,
            quiet=args.q, should_yield=(not args.noyield), run_once=args.run_once)
    elif args.mode == 'client':
        run_client(sbrx=args.rx, sbtx=args.tx, host=args.host, port=args.port,
            quiet=args.q, should_yield=(not args.noyield))
    else:
        raise ValueError(f"Invalid mode: {args.mode}")


def sb2bytes(p):
    # construct a bytes object from a Switchboard packet
    arr = np.concatenate((
        np.array([p.destination, p.flags], dtype=np.uint32),
        p.data.view(np.uint32)
    ))
    return arr.tobytes()


def bytes2sb(b):
    # construct a Switchboard packet from a bytes object
    arr = np.frombuffer(b, dtype=np.uint32)
    return PySbPacket(arr[0], arr[1], arr[2:].view(np.uint8))


def convert_to_queue(q, name, cls):
    if isinstance(q, cls) or (q is None):
        # note that None is passed through
        return q
    elif isinstance(q, str):
        if q == "":
            return None
        else:
            return cls(q)
    else:
        raise TypeError(f'{name} must be a string or {cls.__name__}; got {type(q)}')


def start_tcp_bridge(mode, tx=None, rx=None, host='localhost', port=5555, quiet=True):
    kwargs = dict(
        sbrx=rx,
        sbtx=tx,
        host=host,
        port=port,
        quiet=quiet
    )

    if mode == 'server':
        target = run_server
    elif mode == 'client':
        target = run_client
    else:
        raise ValueError(f"Invalid mode: {mode}")

    import multiprocessing

    p = multiprocessing.Process(target=target, kwargs=kwargs, daemon=True)
    p.start()

    return p


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--rx', type=str, default="", help="URI of the Switchboard queue used in"
        " the SB -> TCP direction.  Optional.")
    parser.add_argument('--tx', type=str, default="", help="URI of the Switchboard queue used in"
        " the TCP -> SB direction.  Optional.")
    parser.add_argument('--mode', type=str, required=True, choices=["server", "client"],
        help="Indicates if this program should act as a TCP server or client.  In each pair"
        " of TCP bridge programs, one must be a server and the other must be a client."
        "  The server will run forever, accepting a new client connection after"
        " the previous client connection terminates.  However, the client only runs")
    parser.add_argument('--port', type=int, default=5555, help="TCP port used for"
        " sending and receiving packets.")
    parser.add_argument('--host', type=str, default="localhost", help="IP address or hostname"
        " used sending/receiving packets.")
    parser.add_argument('-q', action='store_true', help="Quiet mode: doesn't print anything.")
    parser.add_argument('--noyield', action='store_true', help="Reduces latency by keeping the"
        " CPU busy even when there is no packet activity, or when packets are blocked"
        " due to backpressure.")
    parser.add_argument('--run-once', action='store_true',
        help="Process only one connection in server mode, then exit.")

    return parser


if __name__ == "__main__":
    main()
