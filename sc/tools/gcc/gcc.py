from pathlib import Path
import sys


def setup(chip):
    # TODO:
    # - Using ['tool', <tool>, 'input'/'output' to drive input and output names is a huge hack]
    # - These options are all hardcoded for spike plugins. we need to drive these another way.

    tool = 'gcc'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')

    chip.set('tool', tool, 'exe', tool)

    inp = chip.find_files('input', 'plugin')[int(index)]
    plugin_name =  Path(inp).stem
    output = f'outputs/{plugin_name}.so'

    options = []
    if sys.platform == 'darwin':
        options += ['-bundle']
        options += ['-undefined', 'dynamic_lookup']
    else:
        options += ['-shared']

    options += ['-Wall']
    options += ['-Werror']
    options += ['-fPIC']
    options += [inp]
    # TODO: this may not work, since include paths are directories
    options += [f'-I{elem}' for elem in chip.find_files('option', 'idir')]
    options += ['-o', output]

    chip.set('tool', tool, 'option', step, index, options)
