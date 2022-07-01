from pathlib import Path
import sys


def setup(chip):
    tool = 'gcc'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')

    chip.set('tool', tool, 'exe', tool)

    inp = chip.find_files('input', 'plugin')[int(index)]
    plugin_name =  Path(inp).stem
    output = f'outputs/{plugin_name}.so'

    # TODO: These options are hardcoded based on the flags used for Spike
    # plugins in the original mockup. We need a general methodology for
    # supplying flow-specific tool options.

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
    # TODO: Reusing 'idir' here could be problematic if we want to include RTL
    # idirs in the same compilation (either as common config, or b/c software is
    # being built in a flow alongside RTL).
    options += [f'-I{elem}' for elem in chip.find_files('option', 'idir')]
    options += ['-o', output]

    chip.set('tool', tool, 'option', step, index, options)
