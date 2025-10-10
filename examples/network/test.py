#!/usr/bin/env python3

# Example showing how to wire up various modules using SbNetwork

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from umi import sumi
from switchboard import SbNetwork

from pathlib import Path
THIS_DIR = Path(__file__).resolve().parent


def main():
    # create network

    net = SbNetwork(cmdline=True)

    # create the building blocks

    umi_fifo = make_umi_fifo(net)
    umi_fifo.option.set_nodashboard(True)

    umi2axil = make_umi2axil(net)
    umi2axil.option.set_nodashboard(True)

    axil_ram = make_axil_ram(net)
    axil_ram.option.set_nodashboard(True)

    # connect them together

    umi_fifo_i = net.instantiate(umi_fifo)
    umi_fifo_o = net.instantiate(umi_fifo)
    umi2axil_i = net.instantiate(umi2axil)
    axil_ram_i = net.instantiate(axil_ram)

    net.connect(umi_fifo_i.umi_out, umi2axil_i.udev_req)
    net.connect(umi_fifo_o.umi_in, umi2axil_i.udev_resp)

    net.connect(umi2axil_i.axi, axil_ram_i.s_axil)

    net.external(umi_fifo_i.umi_in, txrx='umi')
    net.external(umi_fifo_o.umi_out, txrx='umi')

    # build simulator

    net.build()

    # launch the simulation

    net.simulate()

    # interact with the simulation

    umi = net.intfs['umi']

    wraddr = 0x10
    wrdata = 0xdeadbeef

    umi.write(wraddr, np.uint32(wrdata))

    print(f'Wrote addr=0x{wraddr:x} data=0x{wrdata:x}')

    rdaddr = wraddr

    rddata = umi.read(rdaddr, np.uint32)

    print(f'Read addr=0x{rdaddr:x} data=0x{rddata:x}')

    assert wrdata == rddata


def make_umi_fifo(net):
    dw = 256
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw
    )

    tieoffs = dict(
        bypass="1'b0",
        chaosmode="1'b0",
        fifo_full=None,
        fifo_empty=None,
        vdd="1'b1",
        vss="1'b0"
    )

    interfaces = {
        'umi_in': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'umi_out': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output')
    }

    clocks = [
        'umi_in_clk',
        'umi_out_clk'
    ]

    resets = [
        'umi_in_nreset',
        'umi_out_nreset'
    ]

    from siliconcompiler import Design

    class UmiFifo(Design):
        def __init__(self):
            super().__init__('umi_fifo_wrapper')

            top_module = "umi_fifo"

            from umi.sumi import Fifo
            with self.active_fileset('rtl'):
                self.set_topmodule(top_module)
                self.add_depfileset(Fifo())

            with self.active_fileset('verilator'):
                self.set_topmodule(top_module)
                self.add_depfileset(self, "rtl")

            with self.active_fileset('icarus'):
                self.set_topmodule(top_module)
                self.add_depfileset(self, "rtl")

    dut = net.make_dut(
        design=UmiFifo(),
        fileset="verilator",
        parameters=parameters,
        interfaces=interfaces,
        clocks=clocks,
        resets=resets,
        tieoffs=tieoffs
    )

    #dut.use(sumi)

    #dut.input('sumi/rtl/umi_fifo.v', package='umi')

    return dut


def make_axil_ram(net):
    dw = 64
    aw = 13

    parameters = dict(
        DATA_WIDTH=dw,
        ADDR_WIDTH=aw
    )

    interfaces = {
        's_axil': dict(type='axil', dw=dw, aw=aw, direction='subordinate')
    }

    resets = [dict(name='rst', delay=8)]

    from siliconcompiler import Design

    class AxilRam(Design):
        def __init__(self):
            super().__init__('axil_ram')

            self.set_dataroot(
                name='axil_ram',
                path="git+https://github.com/alexforencich/verilog-axi.git",
                tag="38915fb"
            )
            top_module = "axil_ram"

            with self.active_fileset('rtl'):
                self.add_file('rtl/axil_ram.v')
                self.set_topmodule(top_module)

            with self.active_fileset('verilator'):
                self.set_topmodule(top_module)
                self.add_depfileset(self, "rtl")

            with self.active_fileset('icarus'):
                self.set_topmodule(top_module)
                self.add_depfileset(self, "rtl")

    dut = net.make_dut(
        design=AxilRam(),
        fileset="verilator",
        parameters=parameters,
        interfaces=interfaces,
        resets=resets
    )

    #dut.register_source(
    #    'verilog-axi',
    #    'git+https://github.com/alexforencich/verilog-axi.git',
    #    '38915fb'
    #)

    #dut.input('rtl/axil_ram.v', package='verilog-axi')

    #dut.add('tool', 'verilator', 'task', 'compile', 'warningoff',
    #    ['WIDTHTRUNC', 'TIMESCALEMOD'])

    return dut


def make_umi2axil(net):
    dw = 64
    aw = 64
    cw = 32

    parameters = dict(
        DW=dw,
        AW=aw,
        CW=cw
    )

    interfaces = {
        'udev_req': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input', txrx='umi'),
        'udev_resp': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output', txrx='umi'),
        'axi': dict(type='axil', dw=dw, aw=aw, direction='manager')
    }

    resets = ['nreset']

    from siliconcompiler import Design

    class Umi2Axil(Design):
        def __init__(self):
            super().__init__('umi2axil_wrapper')

            top_module = "umi2axil"

            from umi.adapters import UMI2AXIL
            with self.active_fileset('rtl'):
                self.set_topmodule(top_module)
                self.add_depfileset(UMI2AXIL())

            with self.active_fileset('verilator'):
                self.set_topmodule(top_module)
                self.add_depfileset(self, "rtl")

            with self.active_fileset('icarus'):
                self.set_topmodule(top_module)
                self.add_depfileset(self, "rtl")

    dut = net.make_dut(
        design=Umi2Axil(),
        fileset="verilator",
        parameters=parameters,
        interfaces=interfaces,
        resets=resets
    )

    #dut.use(sumi)

    #dut.input('utils/rtl/umi2axilite.v', package='umi')

    return dut


if __name__ == '__main__':
    main()
