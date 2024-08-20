# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from copy import deepcopy
from itertools import count
from numbers import Integral

from .sbdut import SbDut
from .axi import axi_uris
from .autowrap import (directions_are_compatible, normalize_intf_type,
    type_is_umi, type_is_sb, create_intf_objs, type_is_axi, type_is_axil,
    autowrap, flip_intf, normalize_direction, WireExpr, types_are_compatible)
from .cmdline import get_cmdline_args
from .sbtcp import start_tcp_bridge
from .util import ProcessCollection

from _switchboard import delete_queues


class SbIntf:
    def __init__(self, inst, name, width=None, indices=None):
        self.inst = inst
        self.name = name
        self.width = width

        if (indices is None) and (width is not None):
            indices = slice(width - 1, 0, 1)

        self.slice = indices

    @property
    def intf_def(self):
        return self.inst.block.intf_defs[self.name]

    @property
    def wire_name(self):
        return f'{self.inst.name}_{self.name}'

    def __getitem__(self, key):
        if not isinstance(key, slice):
            key = slice(key, key)

        return SbIntf(inst=self.inst, name=self.name, indices=key)

    def slice_as_str(self):
        if self.slice is None:
            return ''
        else:
            return f'[{self.slice.start}:{self.slice.stop}]'

    def compute_slice_width(self):
        if self.slice.start is not None:
            start = self.slice.start
        else:
            start = self.width - 1

        if self.slice.stop is not None:
            stop = self.slice.stop
        else:
            stop = 0

        return start - stop + 1


class ConstIntf:
    def __init__(self, value):
        self.value = value

    @property
    def intf_def(self):
        return dict(
            type='const',
            direction='output'
        )

    def value_as_str(self, width=None, format='decimal'):
        if width is None:
            width = ''
        else:
            width = str(width)

        if format.lower() == 'decimal':
            return f"{width}'d{self.value}"
        elif format.lower() == 'hex':
            return f"{width}'h{hex(self.value)[2:]}"
        elif format.lower() == 'hex':
            return f"{width}'b{bin(self.value)[2:]}"
        else:
            raise Exception(f'Unsupported format: {format}')


class TcpIntf:
    def __init__(self, intf_def=None, destination=None, **kwargs):
        self.intf_def = intf_def
        self.destination = destination
        self.kwargs = kwargs

    @property
    def wire_name(self):
        if 'port' in self.kwargs:
            retval = f'port_{self.kwargs["port"]}'
            if self.destination is not None:
                retval += f'_{self.destination}'
            return retval


class SbInst:
    def __init__(self, name, block):
        self.name = name
        self.block = block
        self.mapping = {}
        self.external = set()

        for name, value in block.intf_defs.items():
            if value['type'] != 'plusarg':
                self.mapping[name] = dict(uri=None, wire=None)
            width = block.intf_defs[name].get('width', None)
            self.__setattr__(name, SbIntf(inst=self, name=name, width=width))


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

        self.tcp_intfs = {}

        if cmdline:
            self.args = get_cmdline_args(tool=tool, trace=trace, trace_type=trace_type,
                frequency=frequency, period=period, fast=fast, max_rate=max_rate,
                start_delay=start_delay, single_netlist=single_netlist, threads=threads,
                extra_args=extra_args)
        elif args is not None:
            self.args = args

        if hasattr(self, 'args'):
            trace = self.args.trace
            trace_type = self.args.trace_type
            fast = self.args.fast
            tool = self.args.tool
            frequency = self.args.frequency
            period = self.args.period
            max_rate = self.args.max_rate
            start_delay = self.args.start_delay
            single_netlist = self.args.single_netlist
        else:
            # create args object to pass down to SbDut
            from types import SimpleNamespace
            self.args = SimpleNamespace(
                trace=trace,
                trace_type=trace_type,
                fast=fast,
                tool=tool,
                frequency=frequency,
                period=period,
                max_rate=max_rate,
                start_delay=start_delay,
                threads=threads
            )

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

        # keep track of processes started
        self.process_collection = ProcessCollection()

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
        # convert integer inputs into constant datatype
        if isinstance(a, Integral):
            a = ConstIntf(value=a)
        if isinstance(b, Integral):
            b = ConstIntf(value=b)

        # retrieve the two interface definitions
        intf_def_a = a.intf_def
        intf_def_b = b.intf_def

        if intf_def_a is None:
            assert intf_def_b is not None, 'Cannot infer interface type'
            intf_def_a = flip_intf(intf_def_b)

        if intf_def_b is None:
            assert intf_def_a is not None, 'Cannot infer interface type'
            intf_def_b = flip_intf(intf_def_a)

        # make sure that the interfaces are compatible
        type_a = normalize_intf_type(intf_def_a['type'])
        type_b = normalize_intf_type(intf_def_b['type'])
        assert types_are_compatible(type_a, type_b)

        # make sure that the directions are compatible
        direction_a = normalize_direction(type_a, intf_def_a['direction'])
        direction_b = normalize_direction(type_b, intf_def_b['direction'])
        assert directions_are_compatible(
            type_a=type_a, a=direction_a,
            type_b=type_b, b=direction_b
        )

        # indicate which is input vs. output.  we have to look at both type a and
        # type b since one may be a constant
        if (type_a == 'gpio') or (type_b == 'gpio'):
            if (direction_a == 'input') or (direction_b == 'output'):
                input, output = a, b
                direction_a, direction_b = 'input', 'output'
            elif (direction_b == 'input') or (direction_a == 'output'):
                input, output = b, a
                direction_b, direction_a = 'input', 'output'
            else:
                raise Exception(f'Cannot infer connection direction with direction_a={direction_a}'
                    f' and direction_b={direction_b}')

            intf_def_a['direction'] = direction_a
            intf_def_b['direction'] = direction_b

        # determine what the queue will be called that connects the two

        if wire is None:
            if (type_a != 'gpio') and (type_b != 'gpio'):
                wire = f'{a.wire_name}_conn_{b.wire_name}'
            elif not isinstance(output, ConstIntf):
                wire = f'{output.inst.name}_{output.name}'

        if (uri is None) and (wire is not None):
            uri = wire

            if type_is_sb(type_a) or type_is_umi(type_a):
                uri = uri + '.q'

        if (not self.single_netlist) and (type_a != 'gpio') and (type_b != 'gpio'):
            self.register_uri(type=type_a, uri=uri)

        # tell both instances what they are connected to

        if (type_a != 'gpio') and (type_b != 'gpio'):
            if not isinstance(a, TcpIntf):
                a.inst.mapping[a.name]['wire'] = wire
                a.inst.mapping[a.name]['uri'] = uri

            if not isinstance(b, TcpIntf):
                b.inst.mapping[b.name]['wire'] = wire
                b.inst.mapping[b.name]['uri'] = uri
        else:
            if input.inst.mapping[input.name]['wire'] is None:
                expr = WireExpr(input.intf_def['width'])
                input.inst.mapping[input.name]['wire'] = expr

            if isinstance(output, ConstIntf):
                input.inst.mapping[input.name]['wire'].bind(
                    input.slice, output.value_as_str(width=input.compute_slice_width()))
            else:
                input.inst.mapping[input.name]['wire'].bind(
                    input.slice, f'{wire}{output.slice_as_str()}')
                output.inst.mapping[output.name]['wire'] = wire

        # make a note of TCP bridges that need to be started

        for intf, intf_def in [(a, intf_def_a), (b, intf_def_b)]:
            if isinstance(intf, TcpIntf):
                self.add_tcp_intf(intf=intf, intf_def=intf_def, uri=uri)

    def add_tcp_intf(self, intf, intf_def, uri):
        tcp_kwargs = deepcopy(intf.kwargs)

        if 'host' not in tcp_kwargs:
            tcp_kwargs['host'] = 'localhost'

        if 'port' not in tcp_kwargs:
            tcp_kwargs['port'] = 5555

        if 'mode' not in tcp_kwargs:
            tcp_kwargs['mode'] = 'auto'

        if 'quiet' not in tcp_kwargs:
            tcp_kwargs['quiet'] = True

        if 'max_rate' not in intf.kwargs:
            tcp_kwargs['max_rate'] = self.max_rate

        if 'run_once' not in tcp_kwargs:
            tcp_kwargs['run_once'] = False

        tcp_intfs_key = (tcp_kwargs['host'], tcp_kwargs['port'], tcp_kwargs['mode'])

        if tcp_intfs_key not in self.tcp_intfs:
            self.tcp_intfs[tcp_intfs_key] = tcp_kwargs
        else:
            for key, val in self.tcp_intfs[tcp_intfs_key].items():
                if key not in ['inputs', 'outputs']:
                    if val != tcp_kwargs[key]:
                        raise ValueError(f'Mismatch on TCP interface property "{key}".'
                            f'  New value of property is "{tcp_kwargs[key]}"'
                            f' but it was previously set to "{val}".')

        tcp_intf = self.tcp_intfs[tcp_intfs_key]

        tcp_direction = intf_def['direction']

        if tcp_direction == 'input':
            assert 'outputs' not in tcp_intf

            if 'inputs' not in tcp_intf:
                tcp_intf['inputs'] = []

            if intf.destination is None:
                input = uri
            else:
                input = (intf.destination, uri)

            tcp_intf['inputs'].append(input)
        elif tcp_direction == 'output':
            assert 'inputs' not in tcp_intf

            if 'outputs' not in tcp_intf:
                tcp_intf['outputs'] = []

            if intf.destination is None:
                destination = '*'
            else:
                destination = intf.destination

            output = (destination, uri)

            tcp_intf['outputs'].append(output)
        else:
            raise Exception(f'Unsupported direction: {tcp_direction}')

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

                # prepend instance name to init interfaces
                for value in intf_defs.values():
                    if value['type'] == 'plusarg':
                        value['wire'] = f"{inst_name}_{value['wire']}"
                        value['plusarg'] = f"{inst_name}_{value['plusarg']}"

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

        assert intf.intf_def is not None, 'Cannot infer interface type'
        intf_def = deepcopy(intf.intf_def)

        # generate URI if needed

        type = intf_def['type']

        if wire is None:
            wire = intf.wire_name

        intf_def['wire'] = wire

        if uri is None:
            uri = wire

            if type_is_sb(type) or type_is_umi(type):
                uri = uri + '.q'

        intf_def['uri'] = uri

        # register the URI to make sure it doesn't collide with anything else

        self.register_uri(type=type, uri=uri)

        # propagate information about the URI mapping

        if not isinstance(intf, TcpIntf):
            intf.inst.mapping[intf.name] = dict(uri=uri, wire=wire)
            intf.inst.external.add(intf.name)

        # set txrx

        intf_def['txrx'] = txrx

        # set max rate

        if self.max_rate is not None:
            intf_def['max_rate'] = self.max_rate

        # save interface

        if name is None:
            name = intf.wire_name

        assert name not in self.intf_defs, \
            f'Network already contains an external interface called "{name}".'

        self.intf_defs[name] = intf_def

        # make a note of TCP bridges that need to be started

        if isinstance(intf, TcpIntf):
            self.add_tcp_intf(intf=intf, intf_def=intf_def, uri=uri)

        return name

    def simulate(self, start_delay=None, run=None, intf_objs=True, plusargs=None):

        # set defaults

        if start_delay is None:
            start_delay = self.start_delay

        if plusargs is None:
            plusargs = []

        # create interface objects

        if self.single_netlist:
            if isinstance(plusargs, dict):
                plusargs_processed = []
                for inst_name, inst_plusargs in plusargs.items():
                    if inst_name == '*':
                        plusargs_processed += inst_plusargs
                    else:
                        for inst_plusarg, value in inst_plusargs:
                            plusargs_processed.append((f"{inst_name}_{inst_plusarg}", value))
                plusargs = plusargs_processed
            process = self.dut.simulate(start_delay=start_delay, run=run,
                intf_objs=intf_objs, plusargs=plusargs)
            self.process_collection.add(process)

            if intf_objs:
                self.intfs = self.dut.intfs
        else:
            if intf_objs:
                self.intfs = create_intf_objs(self.intf_defs)

            if start_delay is not None:
                import time
                start = time.time()

            insts = self.insts.values()

            if len(insts) > 1:
                try:
                    from tqdm import tqdm
                    insts = tqdm(insts)
                except ModuleNotFoundError:
                    pass

            for inst in insts:
                block = inst.block

                for intf_name, props in inst.mapping.items():
                    block.intf_defs[intf_name]['uri'] = props['uri']

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

                if isinstance(plusargs, dict):
                    inst_plusargs = []
                    inst_plusargs += plusargs.get('*', [])
                    inst_plusargs += plusargs.get(inst.name, [])
                else:
                    inst_plusargs = plusargs

                process = block.simulate(start_delay=start_delay, run=inst.name,
                    intf_objs=False, plusargs=inst_plusargs)

                self.process_collection.add(process)

        # start TCP bridges as needed
        for tcp_kwargs in self.tcp_intfs.values():
            process = start_tcp_bridge(**tcp_kwargs)
            self.process_collection.add(process)

        return self.process_collection

    def terminate(
        self,
        stop_timeout=10,
        use_sigint=False
    ):
        self.process_collection.terminate(stop_timeout=stop_timeout, use_sigint=use_sigint)

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

        uris = set(uris)
        intersection = self.uri_set.intersection(uris)

        if len(intersection) > 0:
            raise ValueError('Failed to add the following URI(s) that'
                f' are already in use: {list(intersection)}')

        self.uri_set.update(uris)

        if fresh:
            delete_queues(list(uris))

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
