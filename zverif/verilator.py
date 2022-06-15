from distutils.command.build import build
import shutil
import subprocess
import sys
from pathlib import Path
from zverif.zvconfig import ZvConfig, ZvVerilatorOpts

class ZvVerilator:
    def __init__(self, cfg: ZvConfig):
        self.cfg = cfg

    def build(self):
        # remove old build
        self.clean()

        # create build directory
        build_dir : Path = self.build_dir
        build_dir.mkdir(exist_ok=True, parents=True)

        # convert Verilog to C
        self.verilate()

        # build simulation binary
        self.compile()

    def verilate(self):
        # look up information about this test
        opts = self.cfg.verilator

        # build up the command
        cmd = []
        cmd += ['verilator']  # TODO make generic
        cmd += ['--top', 'zverif_top']  # TODO make generic
        cmd += ['-trace']  # TODO make generic
        cmd += ['-CFLAGS', '-Wno-unknown-warning-option']
        cmd += ['--cc']
        cmd += ['--exe']
        cmd += opts.verilog_sources
        cmd += opts.c_sources

        cmd = [str(elem) for elem in cmd]

        print(cmd)
        subprocess.run(cmd, check=True, cwd=self.build_dir)

    def compile(self):
        cmd = []
        cmd += ['make']
        cmd += ['-C', 'obj_dir']
        cmd += ['-j']
        cmd += ['-f', 'Vzverif_top.mk']
        cmd += ['Vzverif_top']

        cmd = [str(elem) for elem in cmd]

        print(cmd)
        subprocess.run(cmd, check=True, cwd=self.build_dir)

    def run(self, tests, skip=None):
        # set defaults
        if skip is None:
            skip = []

        # figure out what tests we need to run
        if tests is None or (len(tests) == 0):
            tests = list(self.cfg.sw.objs.keys())

        # run each of those tests
        for test in tests:
            if test not in skip:
                self.run_test(test, quiet=True)
    
    def clean(self):
        shutil.rmtree(str(self.build_dir), ignore_errors=True)

    def run_test(self, test, quiet=False):
        # build up the command
        cmd = []
        cmd += [self.build_dir / 'obj_dir' / 'Vzverif_top']  # TODO make generic
        cmd += [f'+firmware={self.cfg.build_dir / "sw" / test / test}.hex']

        cmd = [str(elem) for elem in cmd]

        subprocess.run(cmd, check=True)

    @property
    def build_dir(self):
        return self.cfg.build_dir / 'verilator'