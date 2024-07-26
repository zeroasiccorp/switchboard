# Build and simulation automation built on SiliconCompiler

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

"""Class inheriting from the SiliconCompiler Chip class that can be used for building a
Switchboard-based testbench.

This class is meant to be interacted with like a regular Chip object, but it has some parameters
automatically configured to abstract away setup of files that are required by all Switchboard
testbenches.
"""

import importlib
import subprocess

from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Any

from .switchboard import path as sb_path
from .verilator import verilator_run
from .icarus import icarus_build_vpi, icarus_find_vpi, icarus_run
from .util import plusargs_to_args, binary_run
from .xyce import xyce_flags
from .ams import make_ams_spice_wrapper, make_ams_verilog_wrapper, parse_spice_subckts
from .autowrap import (normalize_clocks, normalize_interfaces, normalize_resets, normalize_tieoffs,
    normalize_parameters, create_intf_objs)
from .cmdline import get_cmdline_args

import siliconcompiler

SB_DIR = sb_path()


class SbDut(siliconcompiler.Chip):
    def __init__(
        self,
        design: str = 'testbench',
        tool: str = 'verilator',
        default_main: bool = True,
        trace: bool = True,
        trace_type: str = 'vcd',
        module: str = None,
        fpga: bool = False,
        xyce: bool = False,
        frequency: float = 100e6,
        period: float = None,
        max_rate: float = -1,
        start_delay: float = None,
        timeunit: str = None,
        timeprecision: str = None,
        warnings: List[str] = None,
        cmdline: bool = False,
        fast: bool = False,
        extra_args: dict = None,
        autowrap: bool = False,
        parameters=None,
        interfaces=None,
        clocks=None,
        resets=None,
        tieoffs=None,
        buildroot=None,
        builddir=None,
        args=None,
        subcomponent=False,
        suffix=None,
        threads=None
    ):
        """
        Parameters
        ----------
        design: string
            Name of the top level chip design module.

        tool: string, optional
            Which tool to use to compile simulator.  Options are "verilator" or
            "icarus".

        default_main: bool, optional
            If True, the default testbench.cc will be used and does not need to
            be provided via the add() function

        trace: bool, optional
            If true, a waveform dump file will be produced using the file type
            specified by `trace_type`.

        trace_type: str, optional
            File type for the waveform dump file. Defaults to vcd.

        module: str, optional
            module containing the siliconcompiler driver for this object

        fpga: bool, optional
            If True, compile using switchboard's library of modules for FPGA emulation,
            rather than the modules for RTL simulation.

        xyce: bool, optional
            If True, compile for xyce co-simulation.

        frequency: float, optional
            If provided, the default frequency of the clock generated in the testbench,
            in seconds.

        period: float, optional
            If provided, the default period of the clock generated in the testbench,
            in seconds.

        max_rate: float, optional
            If provided, the maximum real-world rate that the simulation is allowed to run
            at, in Hz.  Can be useful to encourage time-sharing between many processes and
            for performance modeling when latencies are large and/or variable.

        start_delay: float, optional
            If provided, the real-world time to delay before the first clock tick in the
            simulation.  Can be useful to make sure that programs start at approximately
            the same time and to prevent simulations from stepping on each other's toes
            when starting up.

        warnings: List[str], optional
            If provided, a list of tool-specific warnings to enable.  If not provided, a default
            set of warnings will be included.  Warnings can be disabled by setting this argument
            to an empty list.

        cmdline: bool, optional
            If True, accept configuration settings from the command line, such as "--trace",
            "--tool TOOL", and "--fast".

        fast: bool, optional
            If True, the simulation binary will not be rebuilt if an existing one is found.
            The setting here can be overridden when build() is called by setting its argument
            with the same name.

        extra_args: dict, optional
            If provided and cmdline=True, a dictionary of additional command line arguments
            to be made available.  The keys of the dictionary are the arguments ("-n", "--test",
            etc.) and the values are themselves dictionaries that contain keyword arguments
            accepted by argparse ("action": "store_true", "default": 42, etc.)
        """

        # call the super constructor

        if autowrap and (not subcomponent):
            toplevel = 'testbench'
        else:
            toplevel = design

        super().__init__(toplevel)

        # parse command-line options if desired

        if cmdline:
            self.args = get_cmdline_args(tool=tool, trace=trace, trace_type=trace_type,
                frequency=frequency, period=period, fast=fast, max_rate=max_rate,
                start_delay=start_delay, threads=threads, extra_args=extra_args)
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
            threads = self.args.threads

        # input validation

        if trace_type not in ('vcd', 'fst'):
            raise ValueError('Invalid trace_type, expected one of "vcd" or "fst"')

        # save settings

        self.tool = tool
        self.trace = trace
        self.trace_type = trace_type
        self.fpga = fpga
        self.xyce = False  # is set True by _configure_xyce
        self.warnings = warnings
        self.fast = fast

        if (period is None) and (frequency is not None):
            period = 1 / frequency
        self.period = period
        self.max_rate = max_rate
        self.start_delay = start_delay

        self.threads = threads

        self.timeunit = timeunit
        self.timeprecision = timeprecision

        self.autowrap = autowrap

        if (suffix is None) and subcomponent:
            suffix = f'_unq_{design}'

        self.suffix = suffix

        if suffix is not None:
            self.dut = f'{design}{suffix}'
        else:
            self.dut = design

        self.parameters = normalize_parameters(parameters)
        self.intf_defs = normalize_interfaces(interfaces)
        self.clocks = normalize_clocks(clocks)
        self.resets = normalize_resets(resets)
        self.tieoffs = normalize_tieoffs(tieoffs)

        # initialization

        self.intfs = {}

        # simulator-agnostic settings

        if builddir is None:
            if buildroot is None:
                buildroot = 'build'

            buildroot = Path(buildroot).resolve()

            if subcomponent:
                # the subcomponent build flow is tool-agnostic, producing a single Verilog
                # file as output, as opposed to a simulator binary
                builddir = buildroot / metadata_str(design=design, parameters=parameters)
            else:
                builddir = buildroot / metadata_str(design=design, parameters=parameters,
                    tool=tool, trace=trace, trace_type=trace_type, threads=threads)

        self.set('option', 'builddir', str(Path(builddir).resolve()))

        self.set('option', 'clean', True)  # preserve old behavior

        if not subcomponent:
            if fpga:
                # library dirs
                self.set('option', 'ydir', sb_path() / 'verilog' / 'fpga')
                self.add('option', 'ydir', sb_path() / 'deps' / 'verilog-axi' / 'rtl')

                # include dirs
                self.set('option', 'idir', sb_path() / 'verilog' / 'fpga' / 'include')

            for opt in ['ydir', 'idir']:
                if not fpga:
                    self.set('option', opt, sb_path() / 'verilog' / 'sim')
                self.add('option', opt, sb_path() / 'verilog' / 'common')

            if trace:
                self.set('tool', 'verilator', 'task', 'compile', 'var', 'trace', True)
                self.add('option', 'define', 'SB_TRACE')

            if self.trace_type == 'fst':
                self.add('option', 'define', 'SB_TRACE_FST')

            if tool == 'icarus':
                self._configure_icarus()
            else:
                if module is None:
                    if tool == 'verilator':
                        module = 'siliconcompiler'
                    else:
                        raise ValueError('Must specify the "module" argument,'
                            ' which is the name of the module containing the'
                            ' SiliconCompiler driver for this simulator.')

                self._configure_build(
                    module=module,
                    default_main=default_main,
                    fpga=fpga
                )

            if xyce:
                self._configure_xyce()
        else:
            # special mode that produces a standalone Verilog netlist
            # rather than building/running a simulation

            flowname = 'package'

            self.package_flow = siliconcompiler.Flow(self, flowname)

            from siliconcompiler.tools.surelog import parse
            self.package_flow.node(flowname, 'parse', parse)

            from .sc.sed import remove
            self.package_flow.node(flowname, 'remove', remove)

            from .sc.morty import uniquify
            self.package_flow.node(flowname, 'uniquify', uniquify)

            self.package_flow.edge(flowname, 'parse', 'remove')
            self.package_flow.edge(flowname, 'remove', 'uniquify')

            self.use(self.package_flow)
            self.set('option', 'flow', flowname)

    def _configure_build(
        self,
        module: str,
        default_main: bool = False,
        fpga: bool = False
    ):
        if not fpga:
            self.input(SB_DIR / 'dpi' / 'switchboard_dpi.cc')

        if default_main and (self.tool == 'verilator'):
            self.input(SB_DIR / 'verilator' / 'testbench.cc')

        if fpga and (self.tool == 'verilator'):
            self.set('tool', 'verilator', 'task', 'compile', 'file', 'config',
                sb_path() / 'verilator' / 'config.vlt')
            self.set('tool', 'verilator', 'task', 'compile', 'warningoff', 'TIMESCALEMOD')

        # enable specific warnings that aren't included by default
        if self.tool == 'verilator':
            if self.warnings is None:
                warnings = ['BLKSEQ']
            else:
                warnings = self.warnings

            for warning in warnings:
                self.set('tool', 'verilator', 'task', 'compile', 'option', f'-Wwarn-{warning}')

        self.set('tool', self.tool, 'task', 'compile', 'var', 'cflags',
            ['-Wno-unknown-warning-option'])
        self.set('tool', self.tool, 'task', 'compile', 'dir', 'cincludes', [SB_DIR / 'cpp'])
        self.set('tool', self.tool, 'task', 'compile', 'var', 'ldflags', ['-pthread'])

        if self.trace and (self.tool == 'verilator'):
            self.set('tool', 'verilator', 'task', 'compile', 'var', 'trace_type', self.trace_type)

        if self.tool == 'verilator':
            timeunit = self.timeunit
            timeprecision = self.timeprecision

            if (timeunit is not None) or (timeprecision is not None):
                if timeunit is None:
                    timeunit = '1ps'  # default from Verilator documentation

                if timeprecision is None:
                    timeprecision = '1ps'  # default from Verilator documentation

                timescale = f'{timeunit}/{timeprecision}'
                self.add('tool', 'verilator', 'task', 'compile', 'option', '--timescale')
                self.add('tool', 'verilator', 'task', 'compile', 'option', timescale)

        if (self.threads is not None) and (self.tool == 'verilator'):
            self.add('tool', 'verilator', 'task', 'compile', 'option', '--threads')
            self.add('tool', 'verilator', 'task', 'compile', 'option', str(self.threads))

        self.set('option', 'libext', ['v', 'sv'])

        # Set up flow that compiles RTL
        # TODO: this will be built into SC
        self.set('option', 'flow', 'simflow')

        compile = importlib.import_module(f'{module}.tools.{self.tool}.compile')
        self.node('simflow', 'compile', compile)

    def _configure_icarus(self):
        self.add('option', 'libext', 'sv')
        self.set('tool', 'icarus', 'task', 'compile', 'var', 'verilog_generation', '2012')

        # use dvflow to execute Icarus, but set steplist so we don't run sim
        from siliconcompiler.flows import dvflow
        self.use(dvflow)

        self.set('option', 'flow', 'dvflow')
        self.set('option', 'to', 'compile')

    def _configure_xyce(self):
        if self.xyce:
            # already configured, so return early
            return

        self.add('option', 'define', 'SB_XYCE')

        if self.tool != 'icarus':
            self.input(SB_DIR / 'dpi' / 'xyce_dpi.cc')

            xyce_c_includes, xyce_ld_flags = xyce_flags()

            self.add('tool', self.tool, 'task', 'compile', 'dir', 'cincludes', xyce_c_includes)
            self.add('tool', self.tool, 'task', 'compile', 'var', 'ldflags', xyce_ld_flags)

        # indicate that build is configured for Xyce.  for Icarus simulation, this flag is used
        # to determine whether a VPI object should be built for Xyce
        self.xyce = True

    def find_sim(self):
        if self.tool == 'icarus':
            result_kind = 'vvp'
        else:
            result_kind = 'vexe'

        return self.find_result(result_kind, step='compile')

    def build(self, cwd: str = None, fast: bool = None):
        """
        Parameters
        ---------
        cwd: str, optional
            Working directory for the simulation build

        fast: bool, optional
            If True, the simulation binary will not be rebuilt if an existing one
            is found.  Defaults to the value provided to the SbDut constructor,
            which in turn defaults to False.
        """

        if fast is None:
            fast = self.fast

        if self.tool == 'icarus':
            if (not fast) or (icarus_find_vpi(cwd, name='switchboard') is None):
                icarus_build_vpi(cwd, name='switchboard')
            if self.xyce and ((not fast) or (icarus_find_vpi(cwd, name='xyce') is None)):
                cincludes, ldflags = xyce_flags()
                icarus_build_vpi(cwd, name='xyce', cincludes=cincludes, ldflags=ldflags)

        # if "fast" is set, then we can return early if the
        # simulation binary already exists
        if fast:
            sim = self.find_sim()
            if sim is not None:
                return sim

        # build the wrapper if needed
        if self.autowrap:
            from .autowrap import autowrap

            filename = Path(self.get('option', 'builddir')).resolve() / 'testbench.sv'

            filename.parent.mkdir(exist_ok=True, parents=True)

            instance = f'{self.dut}_i'

            autowrap(
                instances={instance: self.dut},
                parameters={instance: self.parameters},
                interfaces={instance: self.intf_defs},
                clocks={instance: self.clocks},
                resets={instance: self.resets},
                tieoffs={instance: self.tieoffs},
                filename=filename
            )

            self.input(filename)

        # if we get to this point, then we need to rebuild
        # the simulation binary
        self.run()

        return self.find_sim()

    def simulate(
        self,
        plusargs=None,
        args=None,
        extra_args=None,
        cwd: str = None,
        trace: bool = None,
        period: float = None,
        frequency: float = None,
        max_rate: float = None,
        start_delay: float = None,
        run: str = None,
        intf_objs: bool = True
    ) -> subprocess.Popen:
        """
        Parameters
        ----------
        plusargs: str or list or tuple, optional
            additional arguments to pass to simulator that must be preceded
            with a +. These are listed after `args`.

        args: str or list or tuple, optional
            additional arguments to pass to simulator listed before `plusargs` and
            `extra_args`

        extra_args: str or list or tuple, optional
            additional arguments to pass to simulator listed after `args` and
            `plusargs`

        cwd: str, optional
            working directory where simulation binary is saved

        trace: bool, optional
            If true, a waveform dump file will be produced

        period: float, optional
            If provided, the period of the clock generated in the testbench,
            in seconds.
        """

        # set up interfaces if needed

        if max_rate is None:
            max_rate = self.max_rate

        if intf_objs:
            self.intfs = create_intf_objs(self.intf_defs, max_rate=max_rate)

        # set defaults

        if plusargs is None:
            plusargs = []
        else:
            plusargs = deepcopy(plusargs)

        if args is None:
            args = []

        if extra_args is None:
            extra_args = []

        if trace is None:
            trace = self.trace

        if (period is None) and (frequency is not None):
            period = 1 / frequency

        if period is None:
            period = self.period

        if start_delay is None:
            start_delay = self.start_delay

        # build the simulation if necessary

        sim = self.build(cwd=cwd, fast=True)

        # enable tracing if desired.  it's convenient to define +trace
        # when running Icarus Verilog, even though it is not necessary,
        # since logic in the testbench can use that flag to enable/disable
        # waveform dumping in a simulator-agnostic manner.

        if trace:
            carefully_add_plusarg(key='trace', args=args, plusargs=plusargs)

        if period is not None:
            carefully_add_plusarg(key='period', value=period, args=args, plusargs=plusargs)

        if max_rate is not None:
            carefully_add_plusarg(key='max-rate', value=max_rate, args=args, plusargs=plusargs)

        if start_delay is not None:
            carefully_add_plusarg(
                key='start-delay', value=start_delay, args=args, plusargs=plusargs)

        # add plusargs that define queue connections

        for name, value in self.intf_defs.items():
            wire = value.get('wire', None)
            uri = value.get('uri', None)

            if (wire is not None) and (uri is not None):
                plusargs += [(wire, uri)]

        # run-specific configurations (if running the same simulator build multiple times
        # in parallel)

        if run is not None:
            dumpfile = f'{run}.{self.trace_type}'
            plusargs.append(('dumpfile', dumpfile))

        # run the simulation

        p = None

        if self.tool == 'icarus':
            names = ['switchboard']
            modules = []

            if self.xyce:
                names.append('xyce')

            for name in names:
                vpi = icarus_find_vpi(cwd=cwd, name=name)
                assert vpi is not None, f'Could not find VPI binary "{name}"'
                modules.append(vpi)

            # set the trace format
            if self.trace_type == 'fst' and ('-fst' not in extra_args):
                extra_args.append('-fst')

            p = icarus_run(
                sim,
                plusargs=plusargs,
                modules=modules,
                extra_args=args + extra_args
            )
        else:
            # make sure that the simulator was built with tracing enabled
            if trace and not self.trace:
                raise ValueError('Simulator was built without tracing enabled.'
                    '  Please set trace=True in the SbDut and try again.')

            if self.tool == 'verilator':
                p = verilator_run(
                    sim,
                    plusargs=plusargs,
                    args=args
                )
            else:
                p = binary_run(
                    sim,
                    args=plusargs_to_args(plusargs) + args
                )

        # return a Popen object that one can wait() on

        return p

    def input_analog(
        self,
        filename: str,
        pins: List[Dict[str, Any]] = None,
        name: str = None,
        check_name: bool = True,
        dir: str = None
    ):
        """
        Specifies a SPICE subcircuit to be used in a mixed-signal simulation.  This involves
        providing the path to the SPICE file containing the subcircuit definition and describing
        how real-valued outputs in the SPICE subcircuit should be converted to binary values in
        the Verilog simulation (and vice versa for subcircuit inputs).

        Each of these conversions is specified as an entry in the "pins" argument, which is a
        list of dictionaries, each representing a single pin of the SPICE subcircuit.  Each
        dictionary may have the following keys:
        * "name": name of the pin.  Bus notation may be used, e.g. "myBus[7:0]".  In that case,
        it is expected that the SPICE subcircuit has pins corresponding to each bit in the bus,
        e.g. "myBus[0]", "myBus[1]", etc.
        * "type": direction of the pin.  May be "input", "output", or "constant".  If "constant",
        then this pin will not show up the Verilog module definition to be instantiated in user
        code.  Instead, the SPICE subcircuit pin with that name will be tied off to a fixed
        voltage specified in the "value" field (below).
        * "vil": low voltage threshold, below which a real-number voltage from the SPICE
        simulation is considered to be a logical "0".
        * "vih": high voltage threshold, above which a real-number voltage from the SPICE
        simulation is considered to be a logical "1".
        * "vol": real-number voltage to pass to a SPICE subcircuit input when the digital value
        driven is "0".
        * "voh": real-number voltage to pass to a SPICE subcircuit input when the digital value
        driven is "1".
        * "tr": time taken in the SPICE simulation to transition from a logic "0" value to a
        logic "1" value.
        * "tf": time taken in the SPICE simulation to transition from a logic "1" value to a
        logic "0" value.
        * "initial": initial value of a SPICE subcircuit pin.  Currently only implemented for
        subcircuit outputs.  This is sometimes helpful, because there is a slight delay between
        t=0 and the time when the SPICE simulation reports values for its outputs.  Specifying
        "initial" for subcircuit outputs prevents the corresponding digital signals from being
        driven to "X" at t=0.

        Parameters
        ----------
        filename: str
            The path of the SPICE file containing the subcircuit definition.
        pins: List[Dict[str, Any]]
            List of dictionaries, each describing a pin of the subcircuit.
        name: str
            Name of the SPICE subcircuit that will be instantiated in the mixed-signal simulation.
            If not provided, Switchboard guesses that the name is filename stem.  For example,
            if filename="myCircuit.cir", then Switchboard will guess that the subcircuit name
            is "myCircuit"
        check_name: bool
            If True (default), Switchboard parses the provided file to make sure that there
            is a subcircuit definition matching the given name.
        dir: str
            Running a mixed-signal simulation involves creating SPICE and Verilog wrappers.  This
            argument specifies the directory where those wrappers should be written.  If not
            provided, defaults to the directory where filename is located.
        """

        # automatically configures for Xyce co-simulation if not already configured

        self._configure_xyce()

        # set defaults

        if pins is None:
            pins = []

        if name is None:
            # guess the name of the subcircuit from the filename
            guessed = True
            name = Path(filename).stem
        else:
            guessed = False

        if check_name:
            # make sure that a subcircuit matching the provided or guessed
            # name exists in the file provided.  this is not foolproof, since
            # the SPICE parser is minimal and won't consider things like
            # .INCLUDE.  hence, this feature can be disabled by setting
            # check_name=False

            subckts = parse_spice_subckts(filename)

            for subckt in subckts:
                if name.lower() == name.lower():
                    break
            else:
                if guessed:
                    raise Exception(f'Inferred subckt named "{name}" from the filename,'
                        ' however a corresponding subckt definition was not found.  Please'
                        ' specify a subckt name via the "name" argument.')
                else:
                    raise Exception(f'Could not find a subckt definition for "{name}".')

        if dir is None:
            dir = Path(filename).resolve().parent

        spice_wrapper = make_ams_spice_wrapper(
            name=name,
            filename=filename,
            pins=pins,
            dir=dir
        )

        verilog_wrapper = make_ams_verilog_wrapper(
            name=name,
            filename=spice_wrapper,
            pins=pins,
            dir=dir
        )

        self.input(verilog_wrapper)

    def package(self, suffix=None, fast=None):
        # set defaults

        if suffix is None:
            suffix = self.suffix

        if fast is None:
            fast = self.fast

        # see if we can exit early

        if fast:
            package = self.find_package(suffix=suffix)

            if package is not None:
                return package

        # if not, parse with surelog and postprocess with morty

        if suffix:
            self.set('tool', 'morty', 'task', 'uniquify', 'var', 'suffix', suffix)

        self.set('tool', 'sed', 'task', 'remove', 'var', 'to_remove', '`resetall')

        self.run()

        # return the path to the output
        return self.find_package(suffix=suffix)

    def find_package(self, suffix=None):
        if suffix is None:
            return self.find_result('v', step='parse')
        else:
            return self.find_result('v', step='uniquify')


def metadata_str(design: str, tool: str = None, trace: bool = False,
    trace_type: str = None, threads: int = None, parameters: dict = None) -> Path:

    opts = []

    opts += [design]

    if parameters is not None:
        for k, v in parameters.items():
            opts += [k, v]

    if tool is not None:
        opts += [tool]

    if trace:
        assert trace_type is not None
        opts += [trace_type]

    if threads is not None:
        opts += ['threads', threads]

    return '-'.join(str(opt) for opt in opts)


def carefully_add_plusarg(key, args, plusargs, value=None):
    for plusarg in plusargs:
        if isinstance(plusarg, (list, tuple)):
            if (len(plusarg) >= 1) and (key == plusarg[0]):
                return
        elif key == plusarg:
            return

    if f'+{key}' in args:
        return

    if any(elem.startswith(f'+{key}+') for elem in args):
        return

    if any(elem.startswith(f'+{key}=') for elem in args):
        return

    if value is None:
        plusargs.append(key)
    else:
        plusargs.append((key, value))
