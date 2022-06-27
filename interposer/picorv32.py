import glob # TODO: consider managing files using Pathlib?
from pathlib import Path
import os
import sys

import siliconcompiler

mydir = os.path.dirname(__file__)
root = os.path.join(mydir, '..')
scpath = os.path.join(root, 'sc')

def make_chip():
    '''Common configuration.'''
    chip = siliconcompiler.Chip('picorv32')
    chip.set('option', 'scpath', scpath)

    # Common design sources
    chip.set('input', 'verilog', glob.glob('rtl/*.v'))

    chip.load_target('freepdk45_demo')
    chip.load_flow('verilator_compilation')

    return chip

def _collect_apps():
    apps = {}

    # pattern 1: folders containing a mix of C and assembly,
    # along with a linker script.  right now there's just
    # one such example, called "hello"

    name = 'hello'
    folder = f'verif/sw/{name}'
    apps[name] = {
        'sources': glob.glob(f'{folder}/*.c') + glob.glob(f'{folder}/*.s'),
        'include_paths': [folder, 'verif/common'],
        'linker_script': glob.glob(f'{folder}/*.ld'),
        'expect': ['Hello World from core 0!']
    }

    # pattern 2: RISC-V tests from an external source (https://github.com/riscv-software-src/riscv-tests)
    # the tests are included as an unmodified git submodule
    # the test environment (which implements a test pass/fail, among other things)
    # has been modified slightly to account for the custom UART and exit memory map

    skip_set = {'fence_i'}  # certain tests don't work with PicoRV32

    isa_dir =  'verif/sw/riscv-tests/riscv-tests/isa'
    env_dir = 'verif/sw/riscv-tests/riscv-test-env'
    for app in glob.glob(f'{isa_dir}/rv32ui/*.S'):
        if Path(app).stem in skip_set:
            continue

        apps[Path(app).stem] = {
            'sources': app,
            'include_paths': [
                str(Path(app).parent),
                f'{isa_dir}/macros/scalar',
                f'{env_dir}/p',
                'verif/common'
            ],
            'linker_script': glob.glob(f'{env_dir}/p/*.ld'),
            'expect': ['OK']
        }

    return apps

def build_elf(app_name):
    apps = _collect_apps()
    if app_name not in apps:
        sys.exit(1)

    app = apps[app_name]
    chip = siliconcompiler.Chip(app_name)
    chip.set('option', 'scpath', scpath)

    chip.set('input', 'c', app['sources'])
    chip.set('option', 'idir', app['include_paths'])
    chip.set('input', 'ld', app['linker_script'])

    chip.set('tool', 'riscv_gcc', 'var', 'compile', '0', 'abi', 'ilp32')
    chip.set('tool', 'riscv_gcc', 'var', 'compile', '0', 'isa', 'rv32im')

    chip.load_flow('riscv_compile')

    chip.run()

    return {
        'elf': (chip.find_result('elf', step='compile'), app['expect']),
        'hex': (chip.find_result('hex', step='export'), app['expect'])
    }

def spike(elf_path, expect):
    chip = make_chip()
    chip.set('option', 'jobname', 'spike_sim')
    chip.set('option', 'flow', 'spike_simulation')

    plugins = {
        'uart_plugin': '0x10000000',
        'exit_plugin': '0x10000008'
    }
    for plugin, addr in plugins.items():
        chip.add('input', 'plugin', f'verif/spike/{plugin}.c')
        chip.set('tool', 'spike', 'var', 'run_spike', '0', f'{plugin}-address', addr)

    chip.set('input', 'elf', elf_path)

    chip.add('option', 'idir', 'verif/common')

    chip.set('tool', 'spike', 'var', 'run_spike', '0', 'isa', 'rv32im')
    chip.set('tool', 'spike', 'var', 'run_spike', '0', 'expect', expect)

    # TODO: problem with sizing a flow based on inputs: have to load this after
    chip.load_flow('spike_simulation')

    chip.run()

def verify(test=None):
    if test is None:
        test = 'hello'

    chip = make_chip()
    chip.set('option', 'jobname', 'verify')
    chip.set('option', 'flow', 'verilator_compilation')

    # Additional verification sources
    chip.add('input', 'verilog', glob.glob('verif/verilator/*.v'))
    chip.add('input', 'c', glob.glob('verif/verilator/*.cc'))

    chip.run()

def build():
    chip = make_chip()
    chip.set('option', 'jobname', 'rtl2gds')
    chip.set('option', 'flow', 'asicflow')

    chip.run()

# TODO: (wishlist) have ability to pick target via CLI
# sc picorv32:verify add -> should return status code indicating test success
# sc picorv32:verify hello
# sc picorv32:build
if __name__ == '__main__':
    elf_path, expect = build_elf('hello')['elf']
    spike(elf_path, expect)
    # verify()
    #build()
    pass
