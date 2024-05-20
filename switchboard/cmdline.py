# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

def get_cmdline_args(
    tool: str = 'verilator',
    trace: bool = True,
    trace_type: str = 'vcd',
    frequency: float = 100e6,
    period: float = None,
    max_rate: float = -1,
    start_delay: float = None,
    fast: bool = False,
    single_netlist: bool = False,
    threads: int = None,
    extra_args: dict = None
):
    """
    Sets up and runs a command-line option parser (argparse) using the arguments
    provided as defaults.  The object returned is an argparse.Namespace object,
    which is the same object type returned by ArgumentParser.parse_args()

    This function is used in SbNetwork and SbDut.  It should generally be
    called only once, at the top level of the simulation.

    Parameters
    ----------
    tool: string, optional
        Which tool to use to compile simulator.  Options are "verilator" or
        "icarus".

    trace: bool, optional
        If true, a waveform dump file will be produced using the file type
        specified by `trace_type`.

    trace_type: str, optional
        File type for the waveform dump file. Defaults to vcd.

    frequency: float, optional
        If provided, the default frequency of the clock generated in the testbench,
        in seconds.

    period: float, optional
        If provided, the default period of the clock generated in the testbench,
        in seconds.

    max_rate: float, optional
        If provided, the maximum real-world rate that the simulation is allowed to run
        at, in Hz.  Can be useful to encourage time-sharing between many processes and
        for performance modeling when latencies are large and/or variable.  A value of
        "-1" means that the rate-limiting feature is disabled.

    start_delay: float, optional
        If provided, the real-world time to delay before the first clock tick in the
        simulation.  Can be useful to make sure that programs start at approximately
        the same time and to prevent simulations from stepping on each other's toes
        when starting up.

    fast: bool, optional
        If True, the simulation binary will not be rebuilt if an existing one is found.
        The setting here can be overridden when build() is called by setting its argument
        with the same name.

    extra_args: dict, optional
        If provided and cmdline=True, a dictionary of additional command line arguments
        to be made available.  The keys of the dictionary are the arguments ("-n", "--test",
        etc.) and the values are themselves dictionaries that contain keyword arguments
        accepted by argparse ("action": "store_true", "default": 42, etc.)
    """

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

    parser.add_argument('--max-rate', type=float, default=max_rate,
        help='Maximum real-world rate that the simulation is allowed to run at, in Hz.')

    parser.add_argument('--start-delay', type=float, default=start_delay,
        help='Delay before starting simulation, in seconds.  Can be useful to prevent'
        ' simulations from stepping on each others toes when starting up.')

    if not single_netlist:
        parser.add_argument('--single-netlist', action='store_true', help='Run in single-netlist'
            ' mode, where the network is constructed in Verilog and run in a single simulator.')
    else:
        parser.add_argument('--distributed', action='store_true', help='Run in distributed'
            ' simulation mode, rather than single-netlist mode.')

    parser.add_argument('--threads', type=int, default=threads,
        help='Number of threads to use when running a simulation.')

    if extra_args is not None:
        for k, v in extra_args.items():
            parser.add_argument(k, **v)

    args, _ = parser.parse_known_args()

    # standardize boolean flags

    if trace:
        args.trace = not args.no_trace
        del args.no_trace

    if fast:
        args.fast = not args.rebuild
        del args.rebuild

    if single_netlist:
        args.single_netlist = not args.distributed
        del args.distributed

    # return arguments

    return args
