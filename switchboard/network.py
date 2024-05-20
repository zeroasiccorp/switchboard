# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


from pathlib import Path
from copy import deepcopy
from itertools import count

from .sbdut import SbDut
from .axi import axi_uris
from .autowrap import (directions_are_compatible, normalize_intf_type,
    type_is_umi, type_is_sb, create_intf_objs, type_is_axi, type_is_axil,
    autowrap)
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
        self.external = set()

        for name, value in block.intf_defs.items():
            self.mapping[name] = dict(uri=None, wire=None)
            self.__setattr__(name, SbIntf(inst=self, name=name))


class SbNetwork:
    def __init__(self, cmdline=False, tool: str = 'verilator', trace: bool = False,
        trace_type: str = 'vcd', frequency: float = 100e6, period: float = None,
        max_rate: float = -1, start_delay: float = None, fast: bool = False,
        extra_args: dict = None, cleanup: bool = True, args=None,
        single_netlist: bool = False, threads: int = None, name: str = None):

        self.insts = {}

        self.inst_name_set = set()
        self.inst_name_counters = {}

        self.uri_set = set()
        self.uri_counters = {}

        if cmdline:
            self.args = get_cmdline_args(tool=tool, trace=trace, trace_type=trace_type,
                frequency=frequency, period=period, fast=fast, max_rate=max_rate,
                start_delay=start_delay, single_netlist=single_netlist, threads=threads,
                extra_args=extra_args)
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
            single_netlist = self.args.single_netlist

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

        self.single_netlist = single_netlist

        if single_netlist:
            self.dut = SbDut(args=self.args)
        else:
            self._intf_defs = {}

        self.name = name

        if cleanup:
            import atexit

            def cleanup_func(uri_set=self.uri_set):
                if len(uri_set) > 0:
                    delete_queues(list(uri_set))

            atexit.register(cleanup_func)

    @property
    def intf_defs(self):
        if self.single_netlist:
            return self.dut.intf_defs
        else:
            return self._intf_defs

    def instantiate(self, block, name: str = None):
        # generate a name if needed
        if name is None:
            if isinstance(block, SbDut):
                prefix = block.dut
            else:
                prefix = block.name

            assert prefix is not None, ('Cannot generate name for this instance.'
                '  When block is an SbNetwork, make sure that its constructor set'
                ' "name" if you want name generation to work here.')

            name = self.generate_inst_name(prefix=prefix)

        # make sure the name hasn't been used already
        assert name not in self.inst_name_set

        # add the name to the set of names in use
        self.inst_name_set.add(name)

        # create the instance object
        self.insts[name] = SbInst(name=name, block=block)

        # return the instance object
        return self.insts[name]

    def connect(self, a, b, uri=None, wire=None):
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

        if wire is None:
            wire = f'{a.inst.name}_{a.name}_conn_{b.inst.name}_{b.name}'

        if uri is None:
            uri = wire

            if type_is_sb(type_a) or type_is_umi(type_a):
                uri = uri + '.q'

        if not self.single_netlist:
            # internal connection, no need to register it for cleanup
            self.register_uri(type=type_a, uri=uri)

        # tell both instances what they are connected to

        a.inst.mapping[a.name]['wire'] = wire
        b.inst.mapping[b.name]['wire'] = wire

        a.inst.mapping[a.name]['uri'] = uri
        b.inst.mapping[b.name]['uri'] = uri

    def build(self):
        unique_blocks = set(inst.block for inst in self.insts.values())

        if self.single_netlist:
            passthroughs = [
                ('tool', 'verilator', 'task', 'compile', 'warningoff')
            ]

            for block in unique_blocks:
                self.dut.input(block.package())

                for passthrough in passthroughs:
                    self.dut.add(*passthrough, block.get(*passthrough))

            filename = Path(self.dut.get('option', 'builddir')).resolve() / 'testbench.sv'

            filename.parent.mkdir(exist_ok=True, parents=True)

            # populate the interfaces dictionary
            interfaces = {}

            for inst_name, inst in self.insts.items():
                # make a copy of the interface definitions for this block
                intf_defs = deepcopy(inst.block.intf_defs)

                # wiring
                for intf_name, props in inst.mapping.items():
                    intf_defs[intf_name]['wire'] = props['wire']
                    intf_defs[intf_name]['external'] = intf_name in inst.external

                interfaces[inst_name] = intf_defs

            # generate netlist that connects everything together, and input() it
            self.dut.input(
                autowrap(
                    instances={inst.name: inst.block.dut for inst in self.insts.values()},
                    toplevel='testbench',
                    parameters={inst.name: inst.block.parameters for inst in self.insts.values()},
                    interfaces=interfaces,
                    clocks={inst.name: inst.block.clocks for inst in self.insts.values()},
                    resets={inst.name: inst.block.resets for inst in self.insts.values()},
                    tieoffs={inst.name: inst.block.tieoffs for inst in self.insts.values()},
                    filename=filename
                )
            )

            # build the single-netlist simulation
            self.dut.build()
        else:
            for block in unique_blocks:
                block.build()

    def external(self, intf, name=None, txrx=None, uri=None, wire=None):
        # make a copy of the interface definition since we will be modifying it

        intf_def = deepcopy(intf.inst.block.intf_defs[intf.name])

        # generate URI if needed

        type = intf_def['type']

        if wire is None:
            wire = f'{intf.inst.name}_{intf.name}'

        intf_def['wire'] = wire

        if uri is None:
            uri = wire

            if type_is_sb(type) or type_is_umi(type):
                uri = uri + '.q'

        intf_def['uri'] = uri

        # register the URI to make sure it doesn't collide with anything else

        self.register_uri(type=type, uri=uri)

        # propagate information about the URI mapping

        intf.inst.mapping[intf.name] = dict(uri=uri, wire=wire)
        intf.inst.external.add(intf.name)

        # set txrx

        intf_def['txrx'] = txrx

        # set max rate

        if self.max_rate is not None:
            intf_def['max_rate'] = self.max_rate

        # save interface

        if name is None:
            name = f'{intf.inst.name}_{intf.name}'

        assert name not in self.intf_defs, \
            f'Network already contains an external interface called "{name}".'

        self.intf_defs[name] = intf_def

        return name

    def simulate(self, start_delay=None, run=None, intf_objs=True):
        # set defaults

        if start_delay is None:
            start_delay = self.start_delay

        # create interface objects

        if self.single_netlist:
            self.dut.simulate(start_delay=start_delay, run=run, intf_objs=intf_objs)

            if intf_objs:
                self.intfs = self.dut.intfs
        else:
            if intf_objs:
                self.intfs = create_intf_objs(self.intf_defs)

            if start_delay is not None:
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

                for intf_name, props in inst.mapping.items():
                    # check that the interface is wired up

                    uri = props['uri']

                    if uri is None:
                        raise Exception(f'{inst.name}.{intf_name} not connected')

                    block.intf_defs[intf_name]['uri'] = uri

                # calculate the start delay for this process by measuring the
                # time left until the start delay for the whole network is over

                if start_delay is not None:
                    now = time.time()
                    dt = now - start
                    if dt < start_delay:
                        start_delay = start_delay - dt
                    else:
                        start_delay = None
                else:
                    start_delay = None

                # launch an instance of simulation
                block.simulate(start_delay=start_delay, run=inst.name, intf_objs=False)

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

    def make_dut(self, *args, **kwargs):
        # argument customizations

        cfg = {}

        cfg['args'] = self.args

        if self.single_netlist:
            cfg['autowrap'] = False
            cfg['subcomponent'] = True
        else:
            cfg['autowrap'] = True
            cfg['subcomponent'] = False

        # add to keyword arguments without clobbering
        # existing entries

        kwargs = deepcopy(kwargs)

        for k, v in cfg.items():
            if k not in kwargs:
                kwargs[k] = v

        return SbDut(*args, **kwargs)
