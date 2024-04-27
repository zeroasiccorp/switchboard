from itertools import count

from .sbdut import SbDut
from .autowrap import (directions_are_compatible, normalize_intf_type,
    type_is_umi, type_is_sb)


class SbIntf:
    def __init__(self, inst, name, external=False):
        self.inst = inst
        self.name = name


class SbInst:
    def __init__(self, name, block):
        self.name = name
        self.block = block
        self.mapping = {}
        self.external = {}

        for name, value in block.intf_defs.items():
            self.mapping[name] = None
            self.__setattr__(name, value)


class SbNetwork:
    def __init__(self):
        self.insts = {}
        self.intfs = {}
        self.inst_names = {}
        self.uri_names = {}

    def instantiate(self, block: SbDut, name: str = None):
        if name is None:
            self.generate_name(prefix=block.dut, dict=self.inst_names)

        self.insts[name] = SbInst(name=name, block=block)

        return self.inst_names[name]

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

        # tell both instances what they are connected to
        a.inst.mapping[a.name] = uri
        b.inst.mapping[b.name] = uri

    def build(self):
        unique_blocks = set(inst.block for inst in self.insts)

        for block in unique_blocks:
            block.build()

    def external(self, intf, name=None, txrx=None):
        if name is None:
            if txrx is not None:
                name = txrx
            else:
                name = intf.name

        intf.inst.external[intf.name] = dict(name=name, txrx=txrx)

    def simulate(self):
        # "hard" part
        for inst in self.insts:
            block = inst.block

            for intf, uri in inst.mapping.items():
                # check that the interface is wired up

                if uri is None:
                    raise Exception(f'{inst.name}.{intf.name} not connected')

                block.intf_defs[intf.name]['uri'] = uri

                # mark as internal/external

                block.intf_defs[intf.name]['external'] = intf.name in inst.external

            # launch an instance of simulation
            block.simulate(run=inst.name)

            # map to external interfaces
            for name, value in inst.external.items():
                self.intfs[value['name']] = block.intfs[name]

    @staticmethod
    def generate_name(self, prefix, dict):
        if prefix not in dict:
            dict[prefix] = count(0)

        counter = dict[prefix]

        return f'{prefix}_{next(counter)}'
