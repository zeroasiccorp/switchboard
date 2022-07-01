#!/usr/bin/env python

from pathlib import Path

from zverif.riscv import add_riscv_elf_task, add_riscv_bin_task, add_hex_task
from zverif.spike import add_spike_plugin_task, add_spike_task
from zverif.verilator import add_verilator_build_task, add_verilator_task
from zverif.utils import file_list, calc_task_name
from zverif.config import ZvConfig
from zverif.doit import doit_main_loop

# folder structure 
TOP_DIR = Path(__file__).resolve().parent.parent
RTL_DIR = TOP_DIR / 'rtl'
VERIF_DIR = TOP_DIR / 'verif'
SW_DIR = VERIF_DIR / 'sw'
VERILATOR_DIR = VERIF_DIR / 'verilator' 
VERILOG_DIR = VERIF_DIR / 'verilog'
VERILOG_AXI = VERILOG_DIR / 'verilog-axi' / 'rtl'

# project configuration
CFG = ZvConfig()

def gen_tasks():
    tasks = {}

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
        add_spike_plugin_task(
            tasks=tasks,
            name=name,
            sources=VERIF_DIR / 'spike' / f'{name}.c',
            include_paths=VERIF_DIR / 'common'
        )
        # the 'targets' key is mapped to a list of outputs
        # created by the task.  in this case there's just one,
        # which is the shared object (*.so) plugin
        shared_object = tasks[calc_task_name('spike_plugin', name)].targets[0]
        plugins[str(shared_object)] = addr

    # build verilator: this only needed to be done if there are
    # RTL changes, since the same Verilator binary is reused
    # for running arbitrary RISC-V programs

    add_verilator_build_task(
        tasks=tasks,
        sources = [
            VERILATOR_DIR / '*.vlt',
            RTL_DIR / '*.v',
            VERILOG_AXI / 'arbiter.v',
            VERILOG_AXI / 'priority_encoder.v',
            VERILOG_AXI / 'axil_interconnect.v',
            VERILOG_AXI / 'axil_dp_ram.v',
            VERILOG_DIR / 'axil_interconnect_wrap_*.v',
            VERILOG_DIR / 'zverif_top.v',
            VERIF_DIR / 'verilator' / 'testbench.cc'
        ],
        libs = ['zmq']
    )

    # build an ELF for each RISC-V application

    apps = []

    # pattern 1: folders containing a mix of C and assembly,
    # along with a linker script.  right now there's just
    # one such example, called "hello"

    name = 'hello'
    folder = SW_DIR / name
    add_riscv_elf_task(
        tasks=tasks,
        name=name,
        sources=[folder / '*.c', folder / '*.s'],
        include_paths=[folder, VERIF_DIR / 'common'],
        linker_script=folder / '*.ld'
    )
    apps.append((name, ['Hello World from core 0!']))
    
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

        add_riscv_elf_task(
            tasks=tasks,
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

        apps.append((app.stem, ['OK']))
    
    # add per-application tasks
    for app, expect in apps:
        # task to generate a "bin" file for a particular app
        add_riscv_bin_task(tasks, app)

        # task to generate a "hex" file for a particular app
        add_hex_task(tasks, app)

        # task to run Spike emulation for a particular app
        add_spike_task(tasks, app, plugins=plugins, expect=expect)

        # task to run a Verilator simulation for a particular app
        add_verilator_task(tasks, app, files={'firmware': CFG.sw_dir / f'{app}.bin'},
            expect=expect+['ALL TESTS PASSED.'])

    # output is an iterable of Task objects
    return tasks.values()

if __name__ == "__main__":
    doit_main_loop(tasks=gen_tasks())
