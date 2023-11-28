# Build and simulation automation built on SiliconCompiler

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

"""Class inheriting from the SiliconCompiler Chip class that can be used for building a
Switchboard-based testbench.

This class is meant to be interacted with like a regular Chip object, but it has some parameters
automatically configured to abstract away setup of files that are required by all Switchboard
testbenches.
"""

import importlib
import subprocess

from .switchboard import path as sb_path
from .verilator import verilator_run
from .icarus import icarus_build_vpi, icarus_find_vpi, icarus_run
from .util import plusargs_to_args, binary_run
from .warn import warn_future

import siliconcompiler
from siliconcompiler.flows import dvflow

SB_DIR = sb_path()


class SbDut(siliconcompiler.Chip):
    def __init__(
        self,
        design: str = 'testbench',
        tool: str = 'verilator',
        default_main: bool = None,
        trace: bool = True,
        trace_type: str = 'vcd',
        module: str = None
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
        """
        # call the super constructor

        super().__init__(design)

        # input validation

        if trace_type not in ('vcd', 'fst'):
            raise ValueError('Invalid trace_type, expected one of "vcd" or "fst"')

        if (tool == 'verilator') and (default_main is None):
            default_main = False
            warn_future("default_main isn't provided to the SbDut constructor;"
                ' defaulting to False.  However, we suggest setting default_main=True'
                ' and removing any calls to add() that explicitly add a testbench.cc'
                ' file for Verilator, since that is done automatically when'
                ' default_main=True.  In the future, the default value for default_main'
                ' will be True.')

        # save settings

        self.tool = tool
        self.trace = trace
        self.trace_type = trace_type

        # simulator-agnostic settings

        for opt in ['ydir', 'idir']:
            self.set('option', opt, sb_path() / 'verilog' / 'sim')
            self.add('option', opt, sb_path() / 'verilog' / 'common')

        self.set('option', 'mode', 'sim')

        if trace:
            self.set('option', 'trace', True)

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

            self._configure_dpi(module=module, default_main=default_main)

    def _configure_dpi(
        self,
        module: str,
        default_main: bool = False
    ):
        self.input(SB_DIR / 'dpi' / 'switchboard_dpi.cc')

        if default_main and (self.tool == 'verilator'):
            self.input(SB_DIR / 'verilator' / 'testbench.cc')

        c_flags = ['-Wno-unknown-warning-option']
        c_includes = [SB_DIR / 'cpp']
        ld_flags = ['-pthread']

        self.set('tool', self.tool, 'task', 'compile', 'var', 'cflags', c_flags)
        self.set('tool', self.tool, 'task', 'compile', 'dir', 'cincludes', c_includes)
        self.set('tool', self.tool, 'task', 'compile', 'var', 'ldflags', ld_flags)

        if self.trace and (self.tool == 'verilator'):
            self.set('tool', 'verilator', 'task', 'compile', 'var', 'trace_type', self.trace_type)

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
        self.use(dvflow)
        self.set('option', 'flow', 'dvflow')
        self.set('option', 'to', 'compile')

    def find_sim(self):
        if self.tool == 'icarus':
            result_kind = 'vvp'
        else:
            result_kind = 'vexe'

        return self.find_result(result_kind, step='compile')

    def build(self, cwd: str = None, fast: bool = False):
        """
        Parameters
        ---------
        cwd: str, optional
            Working directory for the simulation build

        fast: bool, optional
            If True, the simulation binary will not be rebuilt if
            an existing one is found
        """

        if self.tool == 'icarus':
            if (not fast) or (icarus_find_vpi(cwd) is None):
                icarus_build_vpi(cwd)

        # if "fast" is set, then we can return early if the
        # simulation binary already exists
        if fast:
            sim = self.find_sim()
            if sim is not None:
                return sim

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
        trace: bool = None
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
        """

        # set defaults

        if plusargs is None:
            plusargs = []

        if args is None:
            args = []

        if extra_args is None:
            extra_args = []

        if trace is None:
            trace = self.trace

        # build the simulation if necessary

        sim = self.build(cwd=cwd, fast=True)

        # enable tracing if desired.  it's convenient to define +trace
        # when running Icarus Verilog, even though it is not necessary,
        # since logic in the testbench can use that flag to enable/disable
        # waveform dumping in a simulator-agnostic manner.

        if trace and ('trace' not in plusargs) and ('+trace' not in args):
            plusargs.append('trace')

        # run the simulation

        p = None

        if self.tool == 'icarus':
            # retrieve the location of the VPI binary
            vpi = icarus_find_vpi(cwd=cwd)
            assert vpi is not None, 'Could not find Switchboard VPI binary.'

            # set the trace format
            if self.trace_type == 'fst' and ('-fst' not in extra_args):
                extra_args.append('-fst')

            p = icarus_run(
                sim,
                plusargs=plusargs,
                modules=[vpi],
                extra_args=extra_args
            )
        else:
            # make sure that the simulator was built with tracing enabled
            if trace and not self.trace:
                raise ValueError('Simulator was built without tracing enabled.'
                    '  Please set trace=True in the SbDut and try again.')

            if self.tool == 'verilator':
                p = verilator_run(sim, plusargs=plusargs)
            else:
                args = plusargs_to_args(plusargs)
                p = binary_run(sim, args=args)

        # return a Popen object that one can wait() on

        return p
