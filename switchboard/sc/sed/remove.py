# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from .sed import setup as setup_tool
from siliconcompiler.tools._common import get_tool_task, input_provides


def setup(chip):
    '''Task that removes specific strings from a Verilog source file.'''

    setup_tool(chip)

    tool = 'sed'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    _, task = get_tool_task(chip, step, index)

    chip.set('tool', tool, 'task', task, 'var', 'to_remove',
             'strings to remove from the Verilog source file',
             field='help')

    design = chip.top()
    if f'{design}.v' in input_provides(chip, step, index):
        chip.set('tool', tool, 'task', task, 'input', f'{design}.v', step=step, index=index)
    else:
        chip.set('tool', tool, 'task', task, 'input', f'{design}.sv', step=step, index=index)
    chip.set('tool', tool, 'task', task, 'output', f'{design}.v', step=step, index=index)


def runtime_options(chip):
    tool = 'sed'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    _, task = get_tool_task(chip, step, index)
    design = chip.top()

    if f'{design}.v' in input_provides(chip, step, index):
        infile = f'inputs/{design}.v'
    else:
        infile = f'inputs/{design}.sv'
    outfile = f'outputs/{design}.v'

    to_remove = chip.get('tool', tool, 'task', task, 'var', 'to_remove', step=step, index=index)

    script = [f's/{elem}//g' for elem in to_remove]
    script += [f'w {outfile}']

    script = '; '.join(script)

    cmdlist = ['-n', f'"{script}"', infile]

    return cmdlist
