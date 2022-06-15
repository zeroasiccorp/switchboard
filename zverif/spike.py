from distutils.command.build import build
import shutil
import subprocess
import sys
from pathlib import Path
from zverif.zvconfig import ZvConfig

class ZvSpike:
    def __init__(self, cfg: ZvConfig):
        self.cfg = cfg

    @property
    def build_dir(self):
        return self.cfg.build_dir / 'spike'

    def task_spike_plugins(self):
        for plugin in self.cfg.spike.objs:
            yield self.build_plugin_task(plugin)

    def build_plugin_task(self, plugin):
        obj = self.cfg.spike.objs[plugin]
        file_dep = [obj.path] + obj.extra_sources
        return {
            'name': plugin,
            'file_dep': file_dep,
            'targets': [self.build_dir / plugin / f'{plugin}.so'],
            'actions': [lambda: self.build_plugin(plugin)],
            'clean': True
        }

    def build_plugin(self, plugin):
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

    def task_spike(self):
        for test in self.cfg.sw.objs:
            yield self.run_spike_task(test)

    def run_spike_task(self, test):
        # collect all plugins
        plugins = [self.build_dir / plugin / f'{plugin}.so'
            for plugin in self.cfg.spike.objs]
        
        # determine ELF for this test
        elf = self.cfg.build_dir / 'sw' / test / f'{test}.elf'

        file_dep = plugins + [elf]
        return {
            'name': test,
            'file_dep': file_dep,
            'actions': [lambda: self.run_spike(test)],
            'uptodate': [False],  # i.e., always run
        }

    def run_spike(self, test):
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
