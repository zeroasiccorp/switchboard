def get_cmdline_args(
    tool: str = 'verilator',
    trace: bool = True,
    trace_type: str = 'vcd',
    frequency: float = 100e6,
    period: float = None,
    fast: bool = False,
    extra_args: dict = None
):
    from argparse import ArgumentParser

    parser = ArgumentParser()

    if not trace:
        parser.add_argument('--trace', action='store_true', help='Probe'
            ' waveforms during simulation.')
    else:
        parser.add_argument('--no-trace', action='store_true', help='Do not'
            ' probe waveforms during simulation.  This can improve build time'
            ' and run time, but reduces visibility.')

    parser.add_argument('--trace-type', type=str, choices=['vcd', 'fst'],
        default=trace_type, help='File type for waveform probing.')

    if not fast:
        parser.add_argument('--fast', action='store_true', help='Do not build'
            ' the simulator binary if it has already been built.')
    else:
        parser.add_argument('--rebuild', action='store_true', help='Build the'
            ' simulator binary even if it has already been built.')

    parser.add_argument('--tool', type=str, choices=['verilator', 'icarus'],
        default=tool, help='Name of the simulator to use.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--period', type=float, default=period,
        help='Period of the clk signal in seconds.  Automatically set if'
        ' --frequency is provided.')
    group.add_argument('--frequency', type=float, default=frequency,
        help='Frequency of the clk signal in Hz.  Automatically set if'
        ' --period is provided.')

    if extra_args is not None:
        for k, v in extra_args.items():
            parser.add_argument(k, **v)

    args = parser.parse_args()

    # standardize boolean flags

    if trace:
        args.trace = not args.no_trace
        del args.no_trace

    if fast:
        args.fast = not args.rebuild
        del args.rebuild

    # return arguments

    return args
