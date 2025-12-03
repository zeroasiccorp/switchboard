# Build and simulation automation built on SiliconCompiler

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

"""Class inheriting from the SiliconCompiler Chip class that can be used for building a
Switchboard-based testbench.

This class is meant to be interacted with like a regular Chip object, but it has some parameters
automatically configured to abstract away setup of files that are required by all Switchboard
testbenches.
"""

import subprocess

from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Any, Union

from .switchboard import path as sb_path
from .icarus import icarus_build_vpi, icarus_find_vpi, icarus_run
from .verilator_run import verilator_run
from .util import plusargs_to_args, binary_run, ProcessCollection
from .ams import make_ams_spice_wrapper, make_ams_verilog_wrapper, parse_spice_subckts
from .autowrap import (normalize_clocks, normalize_interfaces, normalize_resets, normalize_tieoffs,
    normalize_parameters, create_intf_objs, type_is_axi, type_is_axil, type_is_apb)
from .cmdline import get_cmdline_args
from .apb import apb_uris
from .axi import axi_uris

from siliconcompiler import Design, Sim
from siliconcompiler.tools import get_task


SB_DIR = sb_path()


class AutowrapDesign(Design):
    def __init__(
        self,
        design: Design,
        fileset: str,
        parameters=None,
        intf_defs=None,
        clocks=None,
        resets=None,
        tieoffs=None,
        filename=None
    ):

        super().__init__("AutowrapDesign")

        from switchboard.autowrap import autowrap

        instance = f'{design.name}_i'

        autowrap(
            toplevel="testbench",
            instances={instance: design.get_topmodule(fileset=fileset)},
            parameters={instance: parameters},
            interfaces={instance: intf_defs},
            clocks={instance: clocks},
            resets={instance: resets},
            tieoffs={instance: tieoffs},
            filename=filename
        )

        from switchboard.verilog.sim.switchboard_sim import SwitchboardSim

        with self.active_fileset(fileset):
            self.set_topmodule("testbench")
            self.add_depfileset(design)
            self.add_depfileset(SwitchboardSim())
            self.add_file(str(filename))


class SbDut(Sim):
    def __init__(
        self,
        design: Union[Design, str] = None,
        tool: str = 'verilator',
        fileset: str = None,
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

        super().__init__(design)

        self.option.set_nodashboard(True)

        ##########################################
        # parse command-line options if desired
        ##########################################
        if cmdline:
            self.args = get_cmdline_args(
                tool=tool,
                trace=trace,
                trace_type=trace_type,
                frequency=frequency,
                period=period,
                fast=fast,
                max_rate=max_rate,
                start_delay=start_delay,
                threads=threads,
                extra_args=extra_args
            )
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

        self.parameters = normalize_parameters(parameters)
        self.intf_defs = normalize_interfaces(interfaces)
        self.clocks = normalize_clocks(clocks)
        self.resets = normalize_resets(resets)
        self.tieoffs = normalize_tieoffs(tieoffs)

        if not fileset:
            fileset = self.tool

        self.fileset = fileset

        self.design_name = None
        if isinstance(design, Design):
            self.design_name = design.name
        else:
            self.design_name = design

        if (suffix is None) and subcomponent:
            suffix = f'_unq_{self.design_name}'

        self.suffix = suffix

        # initialization

        self.intfs = {}

        # keep track of processes started
        self.process_collection = ProcessCollection()

        # simulator-agnostic settings

        if builddir is None:
            if buildroot is None:
                buildroot = 'build'

            buildroot = Path(buildroot).resolve()

            if subcomponent:
                # the subcomponent build flow is tool-agnostic, producing a single Verilog
                # file as output, as opposed to a simulator binary
                builddir = buildroot / metadata_str(
                    design=self.design_name,
                    parameters=parameters
                )
            else:
                builddir = buildroot / metadata_str(
                    design=self.design_name,
                    parameters=parameters,
                    tool=tool,
                    trace=trace,
                    trace_type=trace_type,
                    threads=threads
                )

        self.option.set_builddir(str(Path(builddir).resolve()))
        # preserve old behavior
        self.option.set_clean(True)

        if not subcomponent:
            if self.tool == 'icarus':
                self._configure_icarus()
            elif self.tool == 'verilator':
                self._configure_verilator()

        else:
            from switchboard.sc.standalone_netlist_flow import StandaloneNetlistFlow
            self.set_flow(StandaloneNetlistFlow())

    def get_topmodule_name(self):
        top_lvl_module_name = None
        main_filesets = self.option.get_fileset()
        if main_filesets and len(main_filesets) != 0:
            main_fileset = main_filesets[0]
            top_lvl_module_name = self.design.get_topmodule(
                fileset=main_fileset
            )

        if self.suffix is not None:
            return f'{top_lvl_module_name}{self.suffix}'
        return top_lvl_module_name

    def _configure_verilator(self):
        from siliconcompiler.flows.dvflow import DVFlow

        self.set_flow(DVFlow(tool="verilator"))
        from siliconcompiler.tools.verilator.compile import CompileTask
        from siliconcompiler.tools.verilator import VerilatorTask

        get_task(self, filter=VerilatorTask).add_warningoff("TIMESCALEMOD")
        get_task(self, filter=VerilatorTask).add_warningoff("WIDTHTRUNC")

        get_task(self, filter=CompileTask).set("var", "cincludes", [SB_DIR / 'cpp'])

        if self.trace:
            get_task(self, filter=CompileTask).set("var", "trace", True)
            get_task(self, filter=CompileTask).set("var", "trace_type", self.trace_type)

        # Set up flow that compiles RTL
        self.set('option', 'to', 'compile')

    def _configure_icarus(self):
        # use dvflow to execute Icarus, but set steplist so we don't run sim
        from siliconcompiler.flows.dvflow import DVFlow

        self.set_flow(DVFlow(tool="icarus"))
        from siliconcompiler.tools.icarus.compile import CompileTask
        get_task(self, filter=CompileTask).set("var", "verilog_generation", "2012")

        self.set('option', 'to', 'compile')

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

        # if "fast" is set, then we can return early if the
        # simulation binary already exists
        if fast:
            self.add_fileset(self.fileset)
            sim = self.find_sim()
            if sim is not None:
                return sim

        # build the wrapper if needed
        if self.autowrap:
            filename = Path(self.option.get_builddir()).resolve() / 'testbench.sv'

            filename.parent.mkdir(exist_ok=True, parents=True)

            wrapped_design = AutowrapDesign(
                design=self.design,
                fileset=self.fileset,
                parameters=self.parameters,
                intf_defs=self.intf_defs,
                clocks=self.clocks,
                resets=self.resets,
                tieoffs=self.tieoffs,
                filename=filename
            )

            self.set_design(wrapped_design)
            self.add_fileset(self.fileset)
        else:
            self.add_fileset(self.fileset)

        assert self.run()

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

        # Add newly created Popen object to subprocess list
        self.process_collection.add(p)

        # return a Popen object that one can wait() on

        return p

    def remove_queues_on_exit(self):
        import atexit
        from _switchboard import delete_queues

        def cleanup_func(uris=self.get_uris()):
            if len(uris) > 0:
                delete_queues(uris)

        atexit.register(cleanup_func)

    def get_uris(self):
        uris = []
        for _, intf in self.intf_defs.items():
            uri = intf.get('uri', None)
            type = intf.get('type', None)
            if uri is not None:
                if type_is_axi(type) or type_is_axil(type):
                    uris.extend(axi_uris(uri))
                elif type_is_apb(type):
                    uris.extend(apb_uris(uri))
                else:
                    uris.append(uri)
        return uris

    def terminate(
        self,
        stop_timeout=10,
        use_sigint=False
    ):
        self.process_collection.terminate(stop_timeout=stop_timeout, use_sigint=use_sigint)

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

    def package(self, suffix: str = None, fast: bool = None) -> str:
        # set defaults

        if suffix is None:
            suffix = self.suffix

        if fast is None:
            fast = self.fast

        # see if we can exit early

        if fast:
            self.add_fileset(self.fileset)
            package = self.find_package(suffix=suffix)

            if package is not None:
                return package

        from switchboard.sc.morty.uniquify import UniquifyVerilogModules
        from switchboard.sc.sed.sed_remove import SedRemove

        # if not, parse with surelog and postprocess with morty

        if suffix:
            get_task(self, filter=UniquifyVerilogModules).set("var", "suffix", suffix)

        get_task(self, filter=SedRemove).set("var", "to_remove", "`resetall")

        self.add_fileset(self.fileset)

        self.run()

        # return the path to the output
        return self.find_package(suffix=suffix)

    def find_package(self, suffix=None) -> str:
        if suffix is None:
            return self.find_result('sv', step='parse')
        else:
            return self.find_result('sv', step='uniquify')


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
