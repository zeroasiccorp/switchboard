import subprocess
import shutil
from pathlib import Path
from zverif.zvconfig import ZvConfig

class ZvVerilator:
    def __init__(self, cfg: ZvConfig):
        self.cfg = cfg

    @property
    def build_dir(self):
        return self.cfg.build_dir / 'verilator'

    def task_verilator_build(self):
        opts = self.cfg.verilator
        return {
            'file_dep': opts.verilog_sources + opts.c_sources,
            'targets': [self.build_dir / 'obj_dir' / 'Vzverif_top'],
            'actions': [self.build]
        }

    def build(self):
        # create a fresh build directory, removing
        # the old one if it exists
        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.build_dir.mkdir(exist_ok=True, parents=True)

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

    def task_verilator(self):
        for test in self.cfg.sw.objs:
            yield self.run_task(test)

    def run_task(self, test):
        file_dep = []
        file_dep += [self.build_dir / 'obj_dir' / 'Vzverif_top']
        file_dep += [self.cfg.build_dir / 'sw' / test / f'{test}.hex']
        return {
            'name': test,
            'file_dep': file_dep,
            'actions': [lambda: self.run(test)],
            'uptodate': [False]  # i.e., always run
        }

    def run(self, test):
        # build up the command
        cmd = []
        cmd += [self.build_dir / 'obj_dir' / 'Vzverif_top']  # TODO make generic
        cmd += [f'+firmware={self.cfg.build_dir / "sw" / test / test}.hex']

        cmd = [str(elem) for elem in cmd]

        subprocess.run(cmd, check=True)
