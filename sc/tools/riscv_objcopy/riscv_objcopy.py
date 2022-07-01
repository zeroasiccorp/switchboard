from zverif.makehex import makehex

def setup(chip):
    tool = 'riscv_objcopy'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')

    chip.set('tool', tool, 'exe', 'riscv64-unknown-elf-objcopy')

    design = chip.get('design')

    input = f'inputs/{design}.elf'
    output = f'outputs/{design}.bin'

    options = []
    options += [f'-O', 'binary']
    options += [input]
    options += [output]

    chip.set('tool', tool, 'option', step, index, options)

def post_process(chip):
    # TODO: this could be a separate step once we support Python-based steps
    design = chip.get('design')
    makehex(f'outputs/{design}.bin')
