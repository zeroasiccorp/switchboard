#!/usr/bin/env python

import os
import sys

from pathlib import Path
from argparse import ArgumentParser

from zverif.umi import UmiPacket

def run(dut, program):
    # assert resetn
    dut.send(UmiPacket(data=0, dstaddr=0x20000000))

    # write program
    with open(program, 'rb') as f:
        data = f.read()
    for addr in range(0, len(data), 4):
        # read a four-byte chunk
        chunk = int.from_bytes(data[addr:addr+4], 'little')
        dut.send(UmiPacket(data=chunk, dstaddr=addr))

    # release resetn
    dut.send(UmiPacket(data=1, dstaddr=0x20000000))

    # handle output
    stdout = ''
    while True:
        packet = dut.recv()

        # process address
        if packet.dstaddr == 0x10000000:
            to_display = chr(packet.data & 0xff)
            stdout += to_display
            print(to_display, end='', flush=True)
        elif packet.dstaddr == 0x10000008:
            kind = packet.data & 0xffff
            if kind == 0x3333:
                exit_code = (packet.data >> 16) & 0xffff
                break
            if kind == 0x5555:
                exit_code = 0
                break
        
    if exit_code != 0:
        print('ERROR!')

    return exit_code, stdout

class DUT:
    def __init__(self, rx_uri, tx_uri):
        self.rx_socket = os.open(rx_uri, os.O_RDONLY)
        self.tx_socket = os.open(tx_uri, os.O_WRONLY)

    def send(self, packet: UmiPacket):        
        # send message
        os.write(self.tx_socket, packet.pack())
    
    def recv(self) -> UmiPacket:
        # receive data
        packet = bytes([])
        while len(packet) < 32:
            packet += os.read(self.rx_socket, 32-len(packet))

        # unpack data
        return UmiPacket.unpack(packet)

def main():
    parser = ArgumentParser()
    parser.add_argument('--rx_port', type=int, default=5556)
    parser.add_argument('--tx_port', type=int, default=5555)
    parser.add_argument('--bin', type=str, default='build/sw/hello.bin')
    parser.add_argument('--expect', type=str, nargs='*')

    args = parser.parse_args()

    dut = DUT(
        rx_uri=f"/tmp/feeds-{args.rx_port}",
        tx_uri=f"/tmp/feeds-{args.tx_port}"
    )

    exit_code, stdout = run(dut, args.bin)
    
    # first check the exit code
    if exit_code != 0:
        sys.exit(exit_code)
    
    # then check the output
    if args.expect is not None:
        for elem in args.expect:
            assert elem in stdout, f'Did not find "{elem}" in output.'

if __name__ == '__main__':
    main()
