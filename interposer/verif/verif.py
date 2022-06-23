#!/usr/bin/env python

from pathlib import Path

from zverif.riscv import riscv_elf_task, riscv_bin_task, hex_task
from zverif.spike import spike_plugin_task, spike_task
from zverif.verilator import verilator_build_task, verilator_task
from zverif.utils import file_list
from zverif.config import ZvConfig
from zverif.doit import doit_main_loop

# folder structure 
TOP_DIR = Path(__file__).resolve().parent.parent
VERIF_DIR = TOP_DIR / 'verif'
RTL_DIR = TOP_DIR / 'rtl'
SW_DIR = TOP_DIR / 'verif' / 'sw'

# project configuration
CFG = ZvConfig()

def gen_tasks():
    # build Spike plugins: each is a shared object (*.so)
    # that is mapped to a particular address.  when Spike
    # is invoked, these compiled plugins and their addresses
    # will be specified as command-line arguments

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
        # the 'targets' key is mapped to a list of outputs
        # created by the task.  in this case there's just one,
        # which is the shared object (*.so) plugin
        plugins[str(task['targets'][0])] = addr
        yield task

    # build verilator: this only needed to be done if there are
    # RTL changes, since the same Verilator binary is reused
    # for running arbitrary RISC-V programs

    yield verilator_build_task(
        sources = [
            RTL_DIR / '*.v',
            VERIF_DIR / 'verilator' / '*.cc',
            VERIF_DIR / 'verilator' / '*.v'
        ]
    )

    # build an ELF for each RISC-V application

    apps = []

    # pattern 1: folders containing a mix of C and assembly,
    # along with a linker script.  right now there's just
    # one such example, called "hello"

    for name in ['hello']:
        folder = SW_DIR / name
        yield riscv_elf_task(
            name=name,
            sources=[folder / '*.c', folder / '*.s'],
            include_paths=[folder, VERIF_DIR / 'common'],
            linker_script=folder / '*.ld'
        )
        apps.append(name)
    
    # pattern 2: RISC-V tests from an external source (https://github.com/riscv-software-src/riscv-tests)
    # the tests are included as an unmodified git submodule
    # the test environment (which implements a test pass/fail, among other things)
    # has been modified slightly to account for the custom UART and exit memory map

    skip_set = {'fence_i'}  # certain tests don't work with PicoRV32

    isa_dir = SW_DIR / 'riscv-tests' / 'riscv-tests' / 'isa'
    env_dir = SW_DIR / 'riscv-tests' / 'riscv-test-env'
    for app in file_list(isa_dir / 'rv32ui' / '*.S'):
        if app.stem in skip_set:
            continue

        yield riscv_elf_task(
            name=app.stem,
            sources=app,
            include_paths=[
                app.parent,
                isa_dir / 'macros' / 'scalar',
                env_dir / 'p',
                VERIF_DIR / 'common'
            ],
            linker_script=env_dir / 'p' / '*.ld'
        )

        apps.append(app.stem)
    
    # add per-application tasks
    for app in apps:
        # task to generate a "bin" file for a particular app
        yield riscv_bin_task(app) 

        # task to generate a "hex" file for a particular app
        yield hex_task(app)

        # task to run Spike emulation for a particular app
        yield spike_task(app, plugins=plugins)

        # task to run a Verilator simulation for a particular app
        yield verilator_task(app, files={'firmware': CFG.sw_dir / f'{app}.hex'})

def main():
    doit_main_loop(tasks=gen_tasks(), group_tasks={
        'elf': 'Build software ELF files.',
        'bin': 'Build software BIN files.',
        'hex': 'Build software HEX files.',
        'spike_plugin': 'Build Spike plugins.',
        'spike': 'Run Spike emulation.',
        'verilator': 'Run Verilator simulation.'
    })

if __name__ == "__main__":
    main()
