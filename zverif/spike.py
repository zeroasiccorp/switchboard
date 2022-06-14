from distutils.command.build import build
import shutil
import subprocess
import sys
from pathlib import Path
from zverif.zvconfig import ZvConfig

class ZvSpike:
    def __init__(self, cfg: ZvConfig):
        self.cfg = cfg

    def build(self, plugins):
        # figure out what plugins we need to build
        if plugins is None or (len(plugins) == 0):
            plugins = self.list()

        # build each of those plugins
        for plugin in plugins:
            self.build_plugin(plugin)

    def run(self, tests):
        # figure out what tests we need to run
        if tests is None or (len(tests) == 0):
            tests = list(self.cfg.sw.objs.keys())

        # run each of those tests
        for test in tests:
            self.run_test(test)

    def list(self):
        return list(self.cfg.spike.objs.keys())
    
    def clean(self, plugins):
        if plugins is None:
            shutil.rmtree(str(self.build_dir), ignore_errors=True)
        else:
            for plugin in plugins:
                shutil.rmtree(str(self.build_dir / plugin), ignore_errors=True)

    def build_plugin(self, plugin):
        # remove old build
        self.clean([plugin])

        # create build directory
        build_dir : Path = self.build_dir / plugin
        build_dir.mkdir(exist_ok=True, parents=True)

        # look up information about this test
        obj = self.cfg.spike.objs[plugin]

        # build up the command
        cmd = []
        cmd += ['gcc']  # TODO make generic
        if sys.platform == 'darwin':
            cmd += ['-bundle']
            cmd += ['-undefined', 'dynamic_lookup']
        else:
            cmd += ['-shared']
        cmd += ['-Wall']
        cmd += ['-Werror']
        cmd += ['-fPIC']
        cmd += obj.extra_sources
        cmd += [obj.path]
        cmd += [f'-I{elem}' for elem in obj.include_paths]
        cmd += ['-o', build_dir / f'{plugin}.so']

        cmd = [str(elem) for elem in cmd]

        print(cmd)
        subprocess.run(cmd, check=True)

    def run_test(self, test):
        # build up the command
        cmd = []
        cmd += ['spike']  # TODO make generic
        cmd += ['-m1']  # TODO make generic
        cmd += ['--isa', self.cfg.riscv.isa]
        for key, val in self.cfg.spike.objs.items():
            cmd += ['--extlib', self.build_dir / key / f'{key}.so']
            cmd += [f'--device={key},{hex(val.address)}']
        cmd += [self.cfg.build_dir / 'sw' / test / f'{test}.elf']

        cmd = [str(elem) for elem in cmd]

        print(cmd)
        subprocess.run(cmd, check=True)   

    @property
    def build_dir(self):
        return self.cfg.build_dir / 'spike'