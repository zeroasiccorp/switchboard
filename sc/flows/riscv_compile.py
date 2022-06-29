def setup(chip):
    '''Simple demo flow for compiling software using RISC-V gcc.

    TODO: this might want to be blackboxed in another flow by a Make step.
    '''
    flow = 'riscv_compile'
    flowpipe = [
        ('import', 'nop'),
        ('compile', 'riscv_gcc'),
        ('export', 'riscv_objcopy')
    ]

    last_step = None
    for step, tool in flowpipe:
        chip.node(flow, step, tool)
        if last_step:
            chip.edge(flow, last_step, step)
        last_step = step

    chip.set('option', 'flow', flow, clobber=False)
