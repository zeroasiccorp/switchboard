import ubelt
from pathlib import Path
from zverif.makehex import makehex
from zverif.zvconfig import ZvConfig
from zverif.utils import get_gcc_deps

class ZvRiscv:
    def __init__(self, cfg: ZvConfig):
        self.cfg = cfg

    @property
    def build_dir(self):
        return self.cfg.build_dir / 'sw'

    def task_elf(self):
        for name in self.cfg.sw.objs:
            yield self.build_elf_task(name)

    def build_elf_task(self, name, auto_file_dep=False):
        obj = self.cfg.sw.objs[name]

        # determine file dependencies.  for now, "auto_file_dep" is
        # too slow to be the default, since dependencies are determined
        # for all software tests.

        file_dep = []

        if auto_file_dep:
            try:
                file_dep += get_gcc_deps(
                    sources=[obj.path]+obj.extra_sources,
                    include_dirs=obj.include_paths,
                    gcc='riscv64-unknown-elf-gcc'  # TODO make generic
                )
            except:
                print(f'Could not determine all dependencies for test: {name}')
                file_dep += [obj.path] + obj.extra_sources
        else:
            file_dep += [obj.path] + obj.extra_sources

        file_dep += [obj.linker_script]

        return {
            'name': name,
            'file_dep': file_dep,
            'targets': [self.build_dir / name / f'{name}.elf'],
            'actions': [lambda: self.build_elf(name)],
            'clean': True
        }

    def build_elf(self, test):
        # create the build directory if needed
        (self.build_dir / test).mkdir(exist_ok=True, parents=True)

        # look up information about this test
        obj = self.cfg.sw.objs[test]

        # build up the command
        cmd = []
        cmd += ['riscv64-unknown-elf-gcc']  # TODO make generic
        cmd += [f'-mabi={self.cfg.riscv.abi}']
        cmd += [f'-march={self.cfg.riscv.isa}']
        cmd += ['-static']
        cmd += ['-mcmodel=medany']
        cmd += ['-fvisibility=hidden']
        cmd += ['-nostdlib']
        cmd += ['-nostartfiles']
        cmd += ['-fno-builtin']
        cmd += [f'-T{obj.linker_script}']
        cmd += obj.extra_sources
        cmd += [obj.path]
        cmd += [f'-I{elem}' for elem in obj.include_paths]
        cmd += ['-o', self.build_dir / test / f'{test}.elf']

        cmd = [str(elem) for elem in cmd]

        info = ubelt.cmd(cmd, check=True)

    def task_bin(self):
        for name in self.cfg.sw.objs:
            yield self.build_bin_task(name)

    def build_bin_task(self, name):
        return {
            'name': name,
            'file_dep': [self.build_dir / name / f'{name}.elf'],
            'targets': [self.build_dir / name / f'{name}.bin'],
            'actions': [lambda: self.build_bin(name)],
            'clean': True
        }

    def build_bin(self, test):
        # build up the command
        cmd = []
        cmd += ['riscv64-unknown-elf-objcopy']  # TODO make generic
        cmd += ['-O', 'binary']
        cmd += [self.build_dir / test / f'{test}.elf']
        cmd += [self.build_dir / test / f'{test}.bin']

        cmd = [str(elem) for elem in cmd]

        info = ubelt.cmd(cmd, check=True)

    def task_hex(self):
        for name in self.cfg.sw.objs:
            yield self.build_hex_task(name)

    def build_hex_task(self, name):
        return {
            'name': name,
            'file_dep': [self.build_dir / name / f'{name}.bin'],
            'targets': [self.build_dir / name / f'{name}.hex'],
            'actions': [lambda: self.build_hex(name)],
            'clean': True
        }

    def build_hex(self, test):
        makehex(self.build_dir / test / f'{test}.bin')
