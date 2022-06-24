def setup(chip):
    flow = 'spike_simulation'
    chip.node(flow, 'import', 'nop')

    # TODO: This is a bit of a hack to try out a dynamic flow on multiple inputs.
    # However, this breaks a whole lot of things:
    # - find_files() on inputs doesn't work properly, since things haven't been
    #   coped into import dir yet
    # - could have weird implications for manifest if we have multiple jobs
    #   that use this flow (is flow job scoped?)
    # - need to call load_flow() after inputs are set up

    for i, _ in enumerate(chip.get('input', 'plugin')):
        step = 'compile_plugin'
        index = str(i)
        chip.node(flow, step, 'gcc', index=index)
        chip.edge(flow, 'import', step, head_index=index)
        chip.edge(flow, step, 'run_spike', tail_index=index)

    chip.node(flow, 'run_spike', 'spike')
