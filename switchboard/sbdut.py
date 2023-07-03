from .switchboard import path as sb_path

import siliconcompiler
from siliconcompiler.tools.verilator import compile

class SbDut(siliconcompiler.Chip):
    """Class inheriting from the SiliconCompiler Chip class that can be used for building a
    Switchboard-based testbench.

    This class is meant to be interacted with like a regular Chip object, but it has some parameters
    automatically configured to abstract away setup of files that are required by all Switchboard
    testbenches.

    Args:
        design (string): Name of the top level chip design module.
    """

    def __init__(self, design):
        super().__init__(design)

        SB_DIR = sb_path()

        self.input(SB_DIR / 'dpi' / 'switchboard_dpi.cc')
        self.set('option', 'ydir', SB_DIR / 'verilog' / 'sim')

        c_flags = ['-Wno-unknown-warning-option']
        c_includes = [SB_DIR / 'cpp']
        ld_flags = ['-pthread']

        self.set('tool', 'verilator', 'task', 'compile', 'var', 'cflags', c_flags)
        self.set('tool', 'verilator', 'task', 'compile', 'dir', 'cincludes', c_includes)
        self.set('tool', 'verilator', 'task', 'compile', 'var', 'ldflags', ld_flags)

        self.set('option', 'mode', 'sim')

        # Set up flow that runs Verilator compile
        # TODO: this will be built into SC
        self.set('option', 'flow', 'simflow')
        self.node('simflow', 'compile', compile)
