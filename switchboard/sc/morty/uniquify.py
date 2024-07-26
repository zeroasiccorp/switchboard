# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from .morty import setup as setup_tool
from siliconcompiler.tools._common import get_tool_task, input_provides


def setup(chip):
    '''Task that uses morty to rewrite a Verilog file with a unique prefix and/or
    suffix for all module definitions.'''

    setup_tool(chip)

    tool = 'morty'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    _, task = get_tool_task(chip, step, index)

    chip.set('tool', tool, 'task', task, 'var', 'suffix',
             'suffix to be added to the end of module names',
             field='help')

    chip.set('tool', tool, 'task', task, 'var', 'prefix',
             'prefix to be added to the beginning of module names',
             field='help')

    design = chip.top()
    if f'{design}.v' in input_provides(chip, step, index):
        chip.set('tool', tool, 'task', task, 'input', f'{design}.v', step=step, index=index)
    else:
        chip.set('tool', tool, 'task', task, 'input', f'{design}.sv', step=step, index=index)
    chip.set('tool', tool, 'task', task, 'output', f'{design}.v', step=step, index=index)


def runtime_options(chip):
    tool = 'morty'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    _, task = get_tool_task(chip, step, index)
    design = chip.top()

    cmdlist = []

    prefix = chip.get('tool', tool, 'task', task, 'var', 'prefix', step=step, index=index)
    if prefix:
        if isinstance(prefix, list) and (len(prefix) == 1) and isinstance(prefix[0], str):
            cmdlist = ['--prefix', prefix[0]] + cmdlist
        else:
            raise ValueError('"prefix" does not have the expected format')

    suffix = chip.get('tool', tool, 'task', task, 'var', 'suffix', step=step, index=index)
    if suffix:
        if isinstance(suffix, list) and (len(suffix) == 1) and isinstance(suffix[0], str):
            cmdlist = ['--suffix', suffix[0]] + cmdlist
        else:
            raise ValueError('"suffix" does not have the expected format')

    if f'{design}.v' in input_provides(chip, step, index):
        infile = f'inputs/{design}.v'
    else:
        infile = f'inputs/{design}.sv'
    outfile = f'outputs/{design}.v'
    cmdlist += ['-o', outfile]

    cmdlist += [infile]

    return cmdlist
