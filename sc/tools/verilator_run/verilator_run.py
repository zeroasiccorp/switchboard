import os

def setup(chip):
    tool = 'verilator_run'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    design = chip.get('design')

    # TODO: big hack
    workdir = chip._getworkdir(step=step, index=index)
    exe_path = os.path.join(workdir, 'inputs', f'{design}.vexe')
    chip.set('tool', tool, 'exe', exe_path)

    options = []
    for var in chip.getkeys('tool', tool, 'var', step, index):
        if var.startswith('+'):
            val = chip.get('tool', tool, 'var', step, index, var)[0]
            options += [f'{var}={val}']
    chip.set('tool', tool, 'option', step, index, options)

def post_process(chip):
    tool = 'verilator_run'
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
