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

    # TODO: we should use something other than 'design' to generate output name,
    # if we want SW compilation steps part of the same job/flowgraph as hardware
    # sim compilation.
    design = chip.get('design')
    output = f'outputs/{design}.elf'

    # TODO: These options are hardcoded based on the flags used for RISC-V
    # software in the original mockup. We need a general methodology for
    # supplying flow-specific tool options.

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
