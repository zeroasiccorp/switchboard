#!/usr/bin/env python3

# Example illustrating how to interact with the umi_fifo module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import sys
import numpy as np

import umi

from switchboard import SbDut, PyUmiPacket, UmiCmd, umi_opcode, UmiRam


MEMORY_SIZE = 32768


def main():
    # build the simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate()

    # run the test: write to random addresses and read back in a random order

    mon = dut.intfs['uhost']

    program_mem = np.fromfile('hello.bin', dtype=np.uint8)
    main_memory = UmiRam(MEMORY_SIZE)
    main_memory.initialize_memory(0, program_mem)

    while True:
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
                    resp = PyUmiPacket(cmd, p.srcaddr, p.dstaddr, main_memory.read(p))
                    mon.send(resp)
            elif p.dstaddr == 0xC0000000:
                c = chr(p.data[0])
                print(c, end='', flush=True)
            elif p.dstaddr == 0xD0000000:
                exit_code = int(p.data.view(np.uint32)[0])
                sys.exit(exit_code)
            else:
                raise ValueError(f'Unsupported address: 0x{p.dstaddr:08x}')

            # send a write reponse if this was an ordinary write (non-posted)
            if opcode == UmiCmd.UMI_REQ_WRITE:
                cmd = (p.cmd & 0xffffffe0) | int(UmiCmd.UMI_RESP_WRITE)
                resp = PyUmiPacket(cmd, p.srcaddr, p.dstaddr)
                mon.send(resp)


def build_testbench():
    interfaces = {
        'uhost_req': dict(type='umi', dw=32, cw=32, aw=64, direction='output', txrx='uhost'),
        'uhost_resp': dict(type='umi', dw=32, cw=32, aw=64, direction='input', txrx='uhost')
    }

    resets = [
        'axilite2umi_resetn',
        dict(name='picorv32_resetn', delay=8)
    ]

    dut = SbDut('dut', autowrap=True, cmdline=True,
        interfaces=interfaces, resets=resets)

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

    dut.build()

    return dut


if __name__ == '__main__':
    main()
