from pathlib import Path

def setup(chip):
    tool = 'spike'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')

    chip.set('tool', tool, 'exe', tool)

    # TODO: set up version parsing

    isa = chip.get('tool', tool, 'var', step, index, 'isa')[0]
    options = []
    options += ['-m1']
    options += ['--isa', isa]
    # TODO: this should really be runtime_options() to support remote processing.
    for plugin in chip.find_files('input', 'plugin'):
        plugin_name = Path(plugin).stem
        inp = f'inputs/{plugin_name}.so'
        address = chip.get('tool', tool, 'var', step, index, f'{plugin_name}-address')[0]
        options += ['--extlib', inp]
        options += [f'--device={plugin_name},{address}']
    options += [chip.find_files('input', 'elf')[0]]

    chip.set('tool', tool, 'option', step, index, options)

def post_process(chip):
    tool = 'spike'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')

    logfile = f'{step}.log'
    with open(logfile, 'r') as f:
        output = f.read()

    expect = chip.get('tool', tool, 'var', step, index, 'expect')

    errors = 0
    for e in expect:
        if e not in output:
            errors += 1

    chip.set('metric', step, index, 'errors', errors)
