def setup(chip):
    '''Simple demo flow for compiling Spike plugins and running Spike.'''
    flow = 'spike_simulation'
    chip.node(flow, 'import', 'nop')

    # TODO: This is a bit of a hack to try out a dynamic flow on multiple inputs.
    # However, this could break some things:
    # - could have weird implications for manifest if we have multiple jobs
    #   that use this flow (is flow job scoped?)
    # - need to call load_flow() after inputs are set up
    #
    # It also feels a bit like it's abusing the indexing system.

    for i, _ in enumerate(chip.get('input', 'plugin')):
        step = 'compile_plugin'
        index = str(i)
        chip.node(flow, step, 'gcc', index=index)
        chip.edge(flow, 'import', step, head_index=index)
        chip.edge(flow, step, 'run_spike', tail_index=index)

    chip.node(flow, 'run_spike', 'spike')
