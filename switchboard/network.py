from copy import deepcopy
from itertools import count

from .sbdut import SbDut
from .axi import delete_axi_queues
from .autowrap import (directions_are_compatible, normalize_intf_type,
    type_is_umi, type_is_sb, create_intf_objs, type_is_axi, type_is_axil)
from .cmdline import get_cmdline_args

from _switchboard import delete_queue


class SbIntf:
    def __init__(self, inst, name):
        self.inst = inst
        self.name = name


class SbInst:
    def __init__(self, name, block):
        self.name = name
        self.block = block
        self.mapping = {}

        for name, value in block.intf_defs.items():
            self.mapping[name] = None
            self.__setattr__(name, SbIntf(inst=self, name=name))


class SbNetwork:
    def __init__(self, cmdline=False, tool: str = 'verilator', trace: bool = True,
        trace_type: str = 'vcd', frequency: float = 100e6, period: float = None,
        fast: bool = False, extra_args: dict = None):

        self.insts = {}
        self.inst_names = {}
        self.uri_names = {}
        self.intf_defs = {}

        if cmdline:
            self.args = get_cmdline_args(tool=tool, trace=trace, trace_type=trace_type,
                period=period, fast=fast, extra_args=extra_args)

    def instantiate(self, block: SbDut, name: str = None):
        if name is None:
            name = self.generate_name(prefix=block.dut, dict=self.inst_names)

        self.insts[name] = SbInst(name=name, block=block)

        return self.insts[name]

    def connect(self, a, b, uri=None):
        # retrieve the two interface definitions
        intf_def_a = a.inst.block.intf_defs[a.name]
        intf_def_b = b.inst.block.intf_defs[b.name]

        # make sure that the interfaces are the same
        type_a = normalize_intf_type(intf_def_a['type'])
        type_b = normalize_intf_type(intf_def_b['type'])
        assert type_a == type_b

        # make sure that the directions are compatible
        assert directions_are_compatible(type=type_a,
            a=intf_def_a['direction'], b=intf_def_b['direction'])

        # determine what the queue will be called that connects the two

        if uri is None:
            prefix = f'{a.inst.name}_conn_{b.inst.name}'
            uri = self.generate_name(prefix=prefix, dict=self.uri_names)
            if type_is_sb(type_a) or type_is_umi(type_a):
                uri = f'{uri}.q'
                delete_queue(uri)
            elif type_is_axi(type_a) or type_is_axil(type_a):
                delete_axi_queues(uri)
            else:
                raise Exception(f'Unsupported interface type: "{type}"')

        # tell both instances what they are connected to
        a.inst.mapping[a.name] = uri
        b.inst.mapping[b.name] = uri

    def build(self):
        unique_blocks = set(inst.block for inst in self.insts.values())

        for block in unique_blocks:
            block.build()

    def external(self, intf, name=None, txrx=None):
        # make a copy of the interface definition since we will be modifying it

        intf_def = deepcopy(intf.inst.block.intf_defs[intf.name])

        # generate URI

        uri = self.generate_name(prefix=intf.name, dict=self.uri_names)

        type = intf_def['type']
        if type_is_sb(type) or type_is_umi(type):
            uri = f'{uri}.q'

        intf_def['uri'] = uri

        intf.inst.mapping[intf.name] = uri

        # set txrx

        intf_def['txrx'] = txrx

        # save interface

        if name is None:
            name = intf.name

        self.intf_defs[name] = intf_def

    def simulate(self):
        # create interface objects

        self.intfs = create_intf_objs(self.intf_defs)

        # "hard" part
        for inst in self.insts.values():
            block = inst.block

            for intf_name, uri in inst.mapping.items():
                # check that the interface is wired up

                if uri is None:
                    raise Exception(f'{inst.name}.{intf_name} not connected')

                block.intf_defs[intf_name]['uri'] = uri

            # launch an instance of simulation
            block.simulate(run=inst.name, intf_objs=False)

    @staticmethod
    def generate_name(prefix, dict):
        if prefix not in dict:
            dict[prefix] = count(0)

        counter = dict[prefix]

        return f'{prefix}_{next(counter)}'
