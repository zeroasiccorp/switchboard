#!/usr/bin/env python3

# Software model of a UMI memory

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


import numpy as np

from switchboard import PyUmiPacket, umi_size, umi_len


class UmiRam:
    """A UMI RAM class"""

    def __init__(self, num_bytes):
        # store the memory size in bytes
        self.mem_size = np.int64(num_bytes)

        # initialize the memory with random data
        self.ram = np.random.randint((2**8 - 1), size=self.mem_size, dtype=np.uint8)

    def check_address(self, addr):
        '''Raises an exception if the provided address is outside of memory.'''

        if addr >= self.mem_size:
            raise ValueError(f"Trying to access addr: {addr} in a memory of size {self.mem_size}")

    def initialize_memory(self, startaddr, data):
        '''Loads data into the memory, starting at startaddr.'''

        endaddr = startaddr + data.size

        # check that the address range is valid
        self.check_address(startaddr)
        self.check_address(endaddr)

        # write data to memory as an array of bytes
        data = data.view(np.uint8)
        self.ram[startaddr:endaddr] = data

    def write(self, packet):
        '''Performs the write transaction specified in packet.'''

        if not isinstance(packet, PyUmiPacket):
            raise TypeError(f"Input: {packet} need to be a PyUmiPacket")

        # remove chipid from the destination address
        startaddr = np.int64(packet.dstaddr & 0xFFFFFFFFFF)
        data = packet.data.view(np.uint8)
        endaddr = startaddr + np.int64(data.size)

        # check that the address range is valid
        self.check_address(startaddr)
        self.check_address(endaddr)

        # perform the write
        self.ram[startaddr:endaddr] = data

    def read(self, packet):
        '''Performs the read transaction specified in packet, returning a NumPy array of bytes.'''

        if not isinstance(packet, PyUmiPacket):
            raise TypeError(f"Input: {packet} need to be a PyUmiPacket")

        # remove chipid from the destination address
        startaddr = np.int64(packet.dstaddr & 0xFFFFFFFFFF)
        data_size = (umi_len(packet.cmd) + 1) << umi_size(packet.cmd)
        endaddr = startaddr + np.int64(data_size)

        # check that the address range is valid
        self.check_address(startaddr)
        self.check_address(endaddr)

        # perform the read and return the result
        return self.ram[startaddr:endaddr]
