# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from copy import deepcopy
from itertools import count

from .sbdut import SbDut
from .axi import axi_uris
from .autowrap import (directions_are_compatible, normalize_intf_type,
    type_is_umi, type_is_sb, create_intf_objs, type_is_axi, type_is_axil)
from .cmdline import get_cmdline_args

from _switchboard import delete_queues


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
    def __init__(self, cmdline=False, tool: str = 'verilator', trace: bool = False,
        trace_type: str = 'vcd', frequency: float = 100e6, period: float = None,
        max_rate: float = None, start_delay: float = None, fast: bool = False,
        extra_args: dict = None, cleanup: bool = True, args=None):

        self.insts = {}

        self.inst_name_set = set()
        self.inst_name_counters = {}

        self.uri_set = set()
        self.uri_counters = {}

        self.intf_defs = {}

        if cmdline:
            self.args = get_cmdline_args(tool=tool, trace=trace, trace_type=trace_type,
                frequency=frequency, period=period, fast=fast, max_rate=max_rate,
                start_delay=start_delay, extra_args=extra_args)
        elif args is not None:
            self.args = args
        else:
            self.args = None

        if self.args is not None:
            trace = self.args.trace
            trace_type = self.args.trace_type
            fast = self.args.fast
            tool = self.args.tool
            frequency = self.args.frequency
            period = self.args.period
            max_rate = self.args.max_rate
            start_delay = self.args.start_delay

        # save settings

        self.tool = tool
        self.trace = trace
        self.trace_type = trace_type
        self.fast = fast

        if (period is None) and (frequency is not None):
            period = 1 / frequency
        self.period = period
        self.max_rate = max_rate
        self.start_delay = start_delay

        if cleanup:
            import atexit

            def cleanup_func(uri_set=self.uri_set):
                if len(uri_set) > 0:
                    delete_queues(list(uri_set))

            atexit.register(cleanup_func)

    def instantiate(self, block: SbDut, name: str = None):
        # generate a name if needed
        if name is None:
            name = self.generate_inst_name(prefix=block.dut)

        # make sure the name hasn't been used already
        assert name not in self.inst_name_set

        # add the name to the set of names in use
        self.inst_name_set.add(name)

        # create the instance object
        self.insts[name] = SbInst(name=name, block=block)

        # return the instance object
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
            uri = f'{a.inst.name}_{a.name}_conn_{b.inst.name}_{b.name}'

            if type_is_sb(type_a) or type_is_umi(type_a):
                uri = uri + '.q'

        self.register_uri(type=type_a, uri=uri)

        # tell both instances what they are connected to
        a.inst.mapping[a.name] = uri
        b.inst.mapping[b.name] = uri

    def build(self):
        unique_blocks = set(inst.block for inst in self.insts.values())

        for block in unique_blocks:
            block.build()

    def external(self, intf, name=None, txrx=None, uri=None):
        # make a copy of the interface definition since we will be modifying it

        intf_def = deepcopy(intf.inst.block.intf_defs[intf.name])

        # generate URI if needed

        type = intf_def['type']

        if uri is None:
            uri = f'{intf.inst.name}_{intf.name}'

            if type_is_sb(type) or type_is_umi(type):
                uri = uri + '.q'

        # register the URI to make sure it doesn't collide with anything else

        self.register_uri(type=type, uri=uri)

        # propagate information about the URI mapping

        intf_def['uri'] = uri

        intf.inst.mapping[intf.name] = uri

        # set txrx

        intf_def['txrx'] = txrx

        # set max rate

        if self.max_rate is not None:
            intf_def['max_rate'] = self.max_rate

        # save interface

        if name is None:
            name = intf.name

        self.intf_defs[name] = intf_def

    def simulate(self):
        # create interface objects

        self.intfs = create_intf_objs(self.intf_defs)

        if self.start_delay is not None:
            import time
            start = time.time()

        insts = self.insts.values()

        try:
            from tqdm import tqdm
            insts = tqdm(insts)
        except ModuleNotFoundError:
            pass

        for inst in insts:
            block = inst.block

            for intf_name, uri in inst.mapping.items():
                # check that the interface is wired up

                if uri is None:
                    raise Exception(f'{inst.name}.{intf_name} not connected')

                block.intf_defs[intf_name]['uri'] = uri

            # calculate the start delay for this process by measuring the
            # time left until the start delay for the whole network is over

            if self.start_delay is not None:
                now = time.time()
                dt = now - start
                if dt < self.start_delay:
                    start_delay = self.start_delay - dt
                else:
                    start_delay = None
            else:
                start_delay = None

            # launch an instance of simulation
            block.simulate(run=inst.name, intf_objs=False, start_delay=start_delay)

    def generate_inst_name(self, prefix):
        if prefix not in self.inst_name_counters:
            self.inst_name_counters[prefix] = count(0)

        counter = self.inst_name_counters[prefix]

        while True:
            name = f'{prefix}_{next(counter)}'

            if name not in self.inst_name_set:
                break

        return name

    def register_uri(self, type, uri, fresh=True):
        if type_is_axi(type) or type_is_axil(type):
            uris = axi_uris(uri)
        else:
            uris = [uri]

        assert self.uri_set.isdisjoint(uris)

        self.uri_set.update(uris)

        if fresh:
            delete_queues(uris)
