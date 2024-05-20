# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from .sed import setup as setup_tool


def setup(chip):
    '''Task that removes specific strings from a Verilog source file.'''

    setup_tool(chip)

    tool = 'sed'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    task = chip._get_task(step, index)

    chip.set('tool', tool, 'task', task, 'var', 'to_remove',
             'strings to remove from the Verilog source file',
             field='help')


def runtime_options(chip):
    tool = 'sed'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    task = chip._get_task(step, index)
    design = chip.top()

    infile = f'inputs/{design}.v'
    outfile = f'outputs/{design}.v'

    to_remove = chip.get('tool', tool, 'task', task, 'var', 'to_remove', step=step, index=index)

    script = [f's/{elem}//g' for elem in to_remove]
    script += [f'w {outfile}']

    script = '; '.join(script)

    cmdlist = ['-n', f'"{script}"', infile]

    return cmdlist
