import shutil
import subprocess
from pathlib import Path

from zverif.makehex import makehex
from zverif.zvconfig import ZvConfig

class ZvRiscv:
    def __init__(self, cfg: ZvConfig):
        self.cfg = cfg

    def build(self, tests):
        # figure out what tests we need to build
        if tests is None or (len(tests) == 0):
            tests = self.list()

        # build each of those tests
        for test in tests:
            self.build_test(test)

    def list(self):
        return list(self.cfg.sw.objs.keys())
    
    def clean(self, tests):
        if tests is None:
            shutil.rmtree(str(self.build_dir), ignore_errors=True)
        else:
            for test in tests:
                shutil.rmtree(str(self.build_dir / test), ignore_errors=True)

    def build_test(self, test):
        # remove old build
        self.clean([test])

        # create build directory
        (self.build_dir / test).mkdir(exist_ok=True, parents=True)

        # build ELF
        self.build_elf(test)

        # build BIN
        self.build_bin(test)

        # build HEX
        self.build_hex(test)

    def build_elf(self, test):
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

        print(cmd)
        subprocess.run(cmd, check=True)

    def build_bin(self, test):
        # build up the command
        cmd = []
        cmd += ['riscv64-unknown-elf-objcopy']  # TODO make generic
        cmd += ['-O', 'binary']
        cmd += [self.build_dir / test / f'{test}.elf']
        cmd += [self.build_dir / test / f'{test}.bin']

        cmd = [str(elem) for elem in cmd]

        print(cmd)
        subprocess.run(cmd, check=True)

    def build_hex(self, test):
        makehex(self.build_dir / test / f'{test}.bin')

    @property
    def build_dir(self):
        return self.cfg.build_dir / 'sw'