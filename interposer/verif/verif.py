#!/usr/bin/env python

import sys
from pathlib import Path

from doit.task import dict_to_task, Task
from doit.cmd_base import TaskLoader2
from doit.doit_cmd import DoitMain

from zverif.riscv import riscv_elf_task, riscv_bin_task, hex_task
from zverif.spike import spike_plugin_task, spike_task
from zverif.verilator import verilator_build_task, verilator_task
from zverif.utils import file_list

# folder structure 
TOP_DIR = Path(__file__).resolve().parent.parent
VERIF_DIR = TOP_DIR / 'verif'
RTL_DIR = TOP_DIR / 'rtl'
SW_DIR = VERIF_DIR / 'sw'

def gen_tasks():
    # build spike plugins

    mmap = {
        'uart_plugin': 0x10000000,
        'exit_plugin': 0x10000008
    }
    plugins = {}
    for name, addr in mmap.items():
        task = spike_plugin_task(
            name=name,
            sources=VERIF_DIR / 'spike' / f'{name}.c',
            include_paths=VERIF_DIR / 'common'
        )
        plugins[str(task['targets'][0])] = addr
        yield task

    # build verilator

    yield verilator_build_task(
        sources = (file_list(RTL_DIR / '*.v') +
            file_list(VERIF_DIR / 'verilator' / '*.cc') + 
            file_list(VERIF_DIR / 'verilator' / '*.v')),
    )

    # build test applications

    tests = []

    hello = SW_DIR / 'hello'
    yield riscv_elf_task(
        name='hello',
        sources=[hello / '*.c', hello / '*.s'],
        include_paths=[hello, VERIF_DIR / 'common'],
        linker_script=hello / '*.ld'
    )
    tests.append('hello')
    
    isa_dir = SW_DIR / 'riscv-tests' / 'riscv-tests' / 'isa'
    env_dir = SW_DIR / 'riscv-tests' / 'riscv-test-env'
    for test in file_list(isa_dir / 'rv32ui' / '*.S'):
        yield riscv_elf_task(
            name=test.stem,
            sources=test,
            include_paths=[
                test.parent,
                isa_dir / 'macros' / 'scalar',
                env_dir / 'p',
                VERIF_DIR / 'common'
            ],
            linker_script=env_dir / 'p' / '*.ld'
        )
        tests.append(test.stem)
    
    # add per-application tasks
    for test in tests:
        yield riscv_bin_task(test)
        yield hex_task(test)
        yield spike_task(test, plugins=plugins)
        yield verilator_task(test, files={'firmware': f'build/sw/{test}.hex'})

def add_group_task(tasks, basename, doc=None):
    # ref: https://github.com/pydoit/doit/blob/419da250f66cebb15ea7db61e745625b3318c29a/doit/loader.py#L327-L344

    group_task = Task(basename, None, doc=doc, has_subtask=True)
    for task in tasks:
        if task.name.startswith(f'{basename}:'):
            group_task.task_dep.append(task.name)
            task.subtask_of = basename
    tasks.append(group_task)

class MyLoader(TaskLoader2):
    def setup(self, opt_values):
        pass

    def load_doit_config(self):
        return {
            'default_tasks': ['verilator:hello'],
            'verbosity': 2
        }

    def load_tasks(self, cmd, pos_args):
        tasks = [dict_to_task(elem) for elem in gen_tasks()]
        add_group_task(tasks, 'elf', 'Build software ELF files.')
        add_group_task(tasks, 'bin', 'Build software BIN files.')
        add_group_task(tasks, 'hex', 'Build software HEX files.')
        add_group_task(tasks, 'spike_plugin', 'Build Spike plugins.')
        add_group_task(tasks, 'spike', 'Run Spike emulation.')
        add_group_task(tasks, 'verilator', 'Run Verilator simulation.')
        return tasks

if __name__ == "__main__":
    sys.exit(DoitMain(MyLoader()).run(sys.argv[1:]))