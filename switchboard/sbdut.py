from pathlib import Path
from .switchboard import path as sb_path
from .verilator import verilator_run
from .icarus import icarus_build_vpi, icarus_run

import siliconcompiler
from siliconcompiler.tools.verilator import compile

from siliconcompiler.flows import dvflow

SB_DIR = sb_path()


class SbDut(siliconcompiler.Chip):
    """Class inheriting from the SiliconCompiler Chip class that can be used for building a
    Switchboard-based testbench.

    This class is meant to be interacted with like a regular Chip object, but it has some parameters
    automatically configured to abstract away setup of files that are required by all Switchboard
    testbenches.

    Args:
        design (string): Name of the top level chip design module.
        tool (string, optional): Which tool to use to compile simulator.  Options are "verilator" or
        "icarus".
    """

    def __init__(self, design, tool: str = 'verilator', default_main: bool = False):
        if tool not in ('verilator', 'icarus'):
            raise ValueError('Invalid tool, expected one of "verilator" or "icarus"')
        self.tool = tool
        self.sim = None

        super().__init__(design)

        for opt in ['ydir', 'idir']:
            self.set('option', opt, sb_path() / 'verilog' / 'sim')
            self.add('option', opt, sb_path() / 'verilog' / 'common')

        self.set('option', 'mode', 'sim')

        if tool == 'verilator':
            self._configure_verilator(default_main=default_main)
        elif tool == 'icarus':
            self._configure_icarus()

    def _configure_verilator(self, default_main: bool = False):
        self.input(SB_DIR / 'dpi' / 'switchboard_dpi.cc')

        if default_main:
            self.input(SB_DIR / 'verilator' / 'testbench.cc')

        c_flags = ['-Wno-unknown-warning-option']
        c_includes = [SB_DIR / 'cpp']
        ld_flags = ['-pthread']

        self.set('tool', 'verilator', 'task', 'compile', 'var', 'cflags', c_flags)
        self.set('tool', 'verilator', 'task', 'compile', 'dir', 'cincludes', c_includes)
        self.set('tool', 'verilator', 'task', 'compile', 'var', 'ldflags', ld_flags)

        # Set up flow that runs Verilator compile
        # TODO: this will be built into SC
        self.set('option', 'flow', 'simflow')
        self.node('simflow', 'compile', compile)

    def _configure_icarus(self):
        self.add('option', 'libext', 'sv')
        self.set('tool', 'icarus', 'task', 'compile', 'var', 'verilog_generation', '2012')

        # use dvflow to execute Icarus, but set steplist so we don't run sim
        self.use(dvflow)
        self.set('option', 'flow', 'dvflow')
        self.set('option', 'to', 'compile')

    def build(self, cwd: str = None):
        result_kind = {'verilator': 'vexe',
                       'icarus': 'vvp'}

        if self.tool == 'icarus':
            icarus_build_vpi(cwd)

        self.run()
        self.sim = self.find_result(result_kind[self.tool], step='compile')
        return self.sim

    def simulate(self, plusargs=None, extra_args=None):
        if self.sim is None:
            self.build()

        p = None
        if self.tool == 'verilator':
            p = verilator_run(self.sim,
                          plusargs=plusargs)
        elif self.tool == 'icarus':
            p = icarus_run(self.sim, plusargs=plusargs,
                       modules=[Path('switchboard_vpi.vpi')],
                       extra_args=extra_args)
        return p
