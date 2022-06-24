def setup(chip):
    flow = 'verilator_compilation'
    chip.node(flow, 'import', 'verilator')
    chip.node(flow, 'compile', 'verilator')
    chip.edge(flow, 'import', 'compile')

    # Pick this flow if option unset, but do not overwrite existing setting.
    chip.set('option', 'flow', flow, clobber=False)
