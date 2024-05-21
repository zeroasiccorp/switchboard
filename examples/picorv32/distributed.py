#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import time
import random
import numpy as np

import umi

from switchboard import SbNetwork, PyUmiPacket, UmiCmd, umi_opcode, UmiRam


FAST = True
NDUTS = 500
DURATION = 35

MEMORY_SIZE = 32768


def main():
    net = SbNetwork(fast=FAST, start_delay=15e-3 * NDUTS)

    # build the simulator
    picorv32 = build_picorv32(net)
    for k in range(NDUTS):
        dut = net.instantiate(picorv32)
        net.external(dut.uhost_req, txrx=f'uhost{k}')
        net.external(dut.uhost_resp, txrx=f'uhost{k}')

    # launch the simulation
    net.build()
    net.simulate()

    # run the test: write to random addresses and read back in a random order

    program_mem = np.fromfile('hello.bin', dtype=np.uint8)
    main_memories = [UmiRam(MEMORY_SIZE) for _ in range(NDUTS)]
    for k in range(NDUTS):
        main_memories[k].initialize_memory(0, program_mem)

    start_time = time.time()
    exit_code = 0

    talked_to_first_core = False

    while time.time() < (start_time + DURATION):
        # pick a random core to interact with
        k = random.randint(0, NDUTS - 1) if talked_to_first_core else 0
        mon = net.intfs[f'uhost{k}']
        main_memory = main_memories[k]

        # UmiTxRx.recv() returns a PyUmiPacket object.  blocking=False means that
        # the method returns None if there is no UMI packet immediately available.
        p = mon.recv(blocking=False)

        if p is not None:
            # make sure that we know how to process this request
            opcode = umi_opcode(p.cmd)
            assert opcode in {UmiCmd.UMI_REQ_READ, UmiCmd.UMI_REQ_WRITE, UmiCmd.UMI_REQ_POSTED}, \
                f'Unsupported opcode: {opcode}'

            if p.dstaddr < MEMORY_SIZE:
                if opcode in {UmiCmd.UMI_REQ_WRITE, UmiCmd.UMI_REQ_POSTED}:
                    main_memory.write(p)
                elif opcode == UmiCmd.UMI_REQ_READ:
                    # change the command to a read response

                    cmd = (p.cmd & 0xffffffe0) | int(UmiCmd.UMI_RESP_READ)
                    resp = PyUmiPacket(cmd, p.srcaddr | (k << 32), p.dstaddr, main_memory.read(p))
                    mon.send(resp)
                    if k == 0:
                        talked_to_first_core = True
            elif p.dstaddr == 0xC0000000:
                c = chr(p.data[0])
                print(c, end='', flush=True, file=sys.stderr)
            elif p.dstaddr == 0xD0000000:
                exit_code = int(p.data.view(np.uint32)[0])
            else:
                raise ValueError(f'Unsupported address: 0x{p.dstaddr:08x}')

            # send a write reponse if this was an ordinary write (non-posted)
            if opcode == UmiCmd.UMI_REQ_WRITE:
                cmd = (p.cmd & 0xffffffe0) | int(UmiCmd.UMI_RESP_WRITE)
                resp = PyUmiPacket(cmd, p.srcaddr | (k << 32), p.dstaddr)
                mon.send(resp)
                if k == 0:
                    talked_to_first_core = True

    print('EXITING', flush=True)
    sys.exit(exit_code)


def build_picorv32(net):
    interfaces = {
        'uhost_req': dict(type='umi', dw=32, cw=32, aw=64, direction='output'),
        'uhost_resp': dict(type='umi', dw=32, cw=32, aw=64, direction='input')
    }

    resets = [
        'axilite2umi_resetn',
        dict(name='picorv32_resetn', delay=8)
    ]

    dut = net.make_dut('dut', trace=False, interfaces=interfaces, resets=resets)

    dut.add('tool', 'verilator', 'task', 'compile', 'file', 'config', 'config.vlt')

    dut.use(umi)
    dut.add('option', 'library', 'umi')
    dut.add('option', 'library', 'lambdalib_stdlib')
    dut.add('option', 'library', 'lambdalib_ramlib')

    dut.register_package_source(
        name='picorv32',
        path='git+https://github.com/YosysHQ/picorv32.git',
        ref='336cfca6e5f1c08788348aadc46b3581b9a5d585'
    )
    dut.input('picorv32.v', package='picorv32')

    dut.input('dut.v')

    dut.add('tool', 'verilator', 'task', 'compile', 'warningoff',
        ['WIDTHEXPAND', 'TIMESCALEMOD'])

    return dut


if __name__ == '__main__':
    main()
