#!/usr/bin/env python3

# Command-line tool that bridges Switchboard packets over TCP.

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

# reference for setting up Python TCP connections:
# https://realpython.com/python-sockets/#echo-client-and-server

# reference for non-blocking socket programming:
# https://stackoverflow.com/a/16745561

import time
import socket
import argparse
import numpy as np
from switchboard import PySbRx, PySbTx, PySbPacket

SB_PACKET_SIZE_BYTES = 60


def tcp2sb(outputs, conn):
    while True:
        # receive data from TCP
        data_rx_from_tcp = bytes([])

        while len(data_rx_from_tcp) < SB_PACKET_SIZE_BYTES:
            b = conn.recv(SB_PACKET_SIZE_BYTES - len(data_rx_from_tcp))

            if len(b) == 0:
                # connection is not alive anymore
                return

            data_rx_from_tcp += b

        # convert to a switchboard packet
        p = bytes2sb(data_rx_from_tcp)

        # figure out which queue this packet is going to
        for rule, output in outputs:
            if rule_matches(rule, p.destination):
                output.send(p)
                break
        else:
            raise Exception(f"No rule for destination {p.destination}")


def sb2tcp(inputs, conn):
    tcp_data_to_send = bytes([])

    while True:
        # get a switchboard packet
        while True:
            # select input and queue its next run as last
            sbrx = inputs.pop(0)
            inputs.append(sbrx)

            # try to receive a packet from this input
            p = sbrx.recv(blocking=False)

            if p is not None:
                break

        # convert the switchboard packet to bytes
        tcp_data_to_send = sb2bytes(p)

        # send the packet out over TCP
        while len(tcp_data_to_send) > 0:
            n = conn.send(tcp_data_to_send)

            if n == 0:
                # connection is not alive anymore
                return

            tcp_data_to_send = tcp_data_to_send[n:]


def run_client(inputs, host, port, quiet=False, max_rate=None):
    """
    Connect to a server, retrying until a connection is made.
    """

    # initialize TX/RX if needed
    inputs = [convert_to_queue(q=input, cls=PySbRx, max_rate=max_rate)
        for input in inputs]

    if not quiet:
        print('Waiting for server', end='', flush=True)
    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
    sb2tcp(inputs=inputs, conn=conn)


def run_server(outputs, host, port=0, quiet=False, max_rate=None, run_once=False):
    """
    Accepts client connections in a loop until Ctrl-C is pressed.
    """

    # initialize TX objects if needed
    outputs = [(rule, convert_to_queue(q=output, cls=PySbTx, max_rate=max_rate))
        for rule, output in outputs]

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
        tcp2sb(outputs=outputs, conn=conn)

        if run_once:
            break


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


def convert_to_queue(q, cls, max_rate=None):
    if isinstance(q, cls):
        # note that None is passed through
        return q
    elif isinstance(q, str):
        # TODO: pass through max_rate
        return cls(q)
    else:
        raise TypeError(f'{q} must be a string or {cls.__name__}; got {type(q)}')


def rule_matches(rule, addr):
    if rule == '*':
        return True
    elif isinstance(rule, int):
        return addr == rule
    elif isinstance(rule, range):
        return rule.start <= addr < rule.stop
    elif isinstance(rule, (list, tuple)):
        # return True if any subrules match
        for subrule in rule:
            if rule_matches(subrule, addr):
                return True

        # otherwise return False
        return False
    else:
        raise Exception(f'Unsupported rule type: {type(rule)}')


def parse_rule(rule):
    subrules = rule.split(',')

    retval = []

    for subrule in subrules:
        if subrule == '*':
            retval.append('*')
        elif '-' in subrule:
            start, stop = subrule.split('-')
            start = int(start)
            stop = int(stop)
            retval.append(range(start, stop + 1))
        else:
            retval.append(int(subrule))

    return retval


def start_tcp_bridge(inputs=None, outputs=None, host='localhost', port=5555,
    quiet=True, max_rate=None):

    kwargs = dict(
        host=host,
        port=port,
        quiet=quiet,
        max_rate=max_rate
    )

    if outputs is not None:
        kwargs['outputs'] = outputs
        target = run_server
    elif inputs is not None:
        kwargs['inputs'] = inputs
        target = run_client
    else:
        raise Exception('Must specify "outputs" or "inputs" argument.')

    import multiprocessing

    p = multiprocessing.Process(target=target, kwargs=kwargs, daemon=True)
    p.start()

    return p


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--outputs', type=str, default=None, nargs='+', help="Space-separated"
        " dictionary of queues to write to.  For example, 0:a.q 1-2:b.q 3,5-7:c.q *:d.q means"
        " that packets sent to destination 0 are routed to a.q, packets sent to destinations 1"
        " or 2 are routed to b.q, packets sent to destinations 3, 5, 6, or 7 are routed to c.q,"
        " and all other packets are routed to d.q")
    parser.add_argument('--inputs', type=str, default=None, nargs='+', help="Space-separated"
        " list of queues to read from, for example a.q b.q c.q")
    parser.add_argument('--port', type=int, default=5555, help="TCP port used for"
        " sending and receiving packets.")
    parser.add_argument('--host', type=str, default="localhost", help="IP address or hostname"
        " used sending/receiving packets.")
    parser.add_argument('-q', action='store_true', help="Quiet mode: doesn't print anything.")
    parser.add_argument('--max-rate', type=float, default=None, help='Maximum rate at which'
        ' queues are read or written.')
    parser.add_argument('--run-once', action='store_true', help="Process only one connection"
        " in server mode, then exit.")

    return parser


def main():
    # parse command-line arguments

    parser = get_parser()
    args = parser.parse_args()

    # main logic

    if args.outputs is not None:
        # parse the output mapping
        outputs = []
        for output in args.outputs:
            rule, output = output.split(':')
            outputs.append((parse_rule(rule), output))

        run_server(outputs=outputs, host=args.host, port=args.port,
            quiet=args.q, max_rate=args.max_rate, run_once=args.run_once)
    elif args.inputs is not None:
        run_client(inputs=args.inputs, host=args.host, port=args.port,
            quiet=args.q, max_rate=args.max_rate)
    else:
        raise ValueError("Must specify either --inputs or --outputs")


if __name__ == "__main__":
    main()
