def setup(chip):
    tool = 'riscv_gcc'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')

    chip.set('tool', tool, 'exe', 'riscv64-unknown-elf-gcc')

    abi = chip.get('tool', tool, 'var', step, index, 'abi')[0]
    isa = chip.get('tool', tool, 'var', step, index, 'isa')[0]
    linker_script = chip.find_files('input', 'ld')[0]
    sources = chip.find_files('input', 'c')
    include_paths = chip.find_files('option', 'idir')
    print('include', include_paths)

    # TODO: what to use as output name?
    design = chip.get('design')
    output = f'outputs/{design}.elf'

    options = []
    options += [f'-mabi={abi}']
    options += [f'-march={isa}']
    options += ['-static']
    options += ['-mcmodel=medany']
    options += ['-fvisibility=hidden']
    options += ['-nostdlib']
    options += ['-nostartfiles']
    options += ['-fno-builtin']
    options += [f'-T{linker_script}']
    options += sources
    options += [f'-I{elem}' for elem in include_paths]
    options += ['-o', output]

    chip.set('tool', tool, 'option', step, index, options)

