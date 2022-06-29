def setup(chip):
    flow = 'verilator_compilation'
    chip.node(flow, 'import', 'verilator')
    chip.node(flow, 'compile', 'verilator')
    chip.node(flow, 'run', 'verilator_run')

    chip.edge(flow, 'import', 'compile')
    chip.edge(flow, 'compile', 'run')

    # Pick this flow if option unset, but do not overwrite existing setting.
    chip.set('option', 'flow', flow, clobber=False)
