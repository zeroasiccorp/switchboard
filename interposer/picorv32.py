import glob # TODO: consider managing files using Pathlib?
import os

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

def spike():
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

    chip.set('input', 'elf', 'zverif-out/sw/hello.elf')

    chip.add('option', 'idir', 'verif/common')

    chip.set('tool', 'spike', 'var', 'run_spike', '0', 'isa', 'rv32im')
    chip.set('tool', 'spike', 'var', 'run_spike', '0', 'expect', ['Hello World from core 0!'])

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
    spike()
    # verify()
    #build()
    pass
