import argparse
import glob # TODO: consider managing files using Pathlib?
import inspect
import os
from pathlib import Path
import sys

import siliconcompiler

mydir = os.path.dirname(__file__)
root = os.path.join(mydir, '..')
scpath = os.path.join(root, 'sc')

def make_chip(design='picorv32'):
    '''Common configuration.

    TODO: The design kwarg shouldn't be necessary -- all targets in this file
    should use the same design name.
    '''
    # TODO: Should we somehow pick up an existing manifest and pull in job
    # history to ensure all runs get recorded? How do we determine what is a
    # "scratch" vs "final" run?
    chip = siliconcompiler.Chip(design)

    # Add setup modules under this repo's sc/ directory to search path
    chip.set('option', 'scpath', scpath)

    # Enable designer to specify SC CLI switches
    chip.create_cmdline('picorv32', switchlist=['-quiet', '-steplist'])

    # Common design sources
    chip.set('input', 'verilog', glob.glob('rtl/*.v'))

    # Load setup modules that may be used
    # TODO: this could be put into a custom target under sc/targets/
    chip.load_target('freepdk45_demo')
    chip.load_flow('verilator_compilation')

    return chip

def _collect_apps():
    apps = {}

    # pattern 1: folders containing a mix of C and assembly,
    # along with a linker script.  right now there's just
    # one such example, called "hello"

    name = 'hello'
    folder = f'verif/sw/{name}'
    apps[name] = {
        'sources': glob.glob(f'{folder}/*.c') + glob.glob(f'{folder}/*.s'),
        'include_paths': [folder, 'verif/common'],
        'linker_script': glob.glob(f'{folder}/*.ld'),
        'expect': ['Hello World from core 0!']
    }

    # pattern 2: RISC-V tests from an external source (https://github.com/riscv-software-src/riscv-tests)
    # the tests are included as an unmodified git submodule
    # the test environment (which implements a test pass/fail, among other things)
    # has been modified slightly to account for the custom UART and exit memory map

    skip_set = {'fence_i'}  # certain tests don't work with PicoRV32

    isa_dir =  'verif/sw/riscv-tests/riscv-tests/isa'
    env_dir = 'verif/sw/riscv-tests/riscv-test-env'
    for app in glob.glob(f'{isa_dir}/rv32ui/*.S'):
        if Path(app).stem in skip_set:
            continue

        apps[Path(app).stem] = {
            'sources': app,
            'include_paths': [
                str(Path(app).parent),
                f'{isa_dir}/macros/scalar',
                f'{env_dir}/p',
                'verif/common'
            ],
            'linker_script': glob.glob(f'{env_dir}/p/*.ld'),
            'expect': ['OK']
        }

    return apps

def build_app(app_name):
    '''Helper to build app by name.

    This runs each indivdual tool (gcc, objcopy) through SC, but this feels a
    little hacky. We may want to blackbox software compilation through Make.

    I also think it would be ideal to make this part of the actual SC flowgraph,
    rather than running it as a separate job. However, we don't have a great way
    to pass in a "design" equivalent for the SW build that's separate from the
    hardware top-level, so doing it as a separate build for now.
    '''
    apps = _collect_apps()
    if app_name not in apps:
        raise ValueError(f'Unsupported app {app} for target verify')

    app = apps[app_name]
    chip = siliconcompiler.Chip(app_name)
    chip.set('option', 'scpath', scpath)

    chip.set('input', 'c', app['sources'])
    chip.set('option', 'idir', app['include_paths'])
    chip.set('input', 'ld', app['linker_script'])

    chip.set('tool', 'riscv_gcc', 'var', 'compile', '0', 'abi', 'ilp32')
    chip.set('tool', 'riscv_gcc', 'var', 'compile', '0', 'isa', 'rv32im')

    chip.load_flow('riscv_compile')

    chip.run()

    return (
        chip.find_result('elf', step='compile'),
        chip.find_result('hex', step='export'),
        app['expect']
    )

def configure_spike(app='hello'):
    chip = make_chip()
    elf_path, _, expect = build_app(app)

    chip.set('option', 'jobname', 'spike_sim')
    chip.set('option', 'flow', 'spike_simulation')

    # Pass in plugin sources + locations as inputs and tool vars, respectively
    plugins = {
        'uart_plugin': '0x10000000',
        'exit_plugin': '0x10000008'
    }
    for plugin, addr in plugins.items():
        chip.add('input', 'plugin', f'verif/spike/{plugin}.c')
        chip.set('tool', 'spike', 'var', 'run_spike', '0', f'{plugin}-address', addr)

    chip.set('input', 'elf', elf_path)

    chip.add('option', 'idir', 'verif/common')

    # Additional tool configuration
    chip.set('tool', 'spike', 'var', 'run_spike', '0', 'isa', 'rv32im')
    chip.set('tool', 'spike', 'var', 'run_spike', '0', 'expect', expect)

    # TODO: problem with sizing a flow based on inputs: have to load this after
    chip.load_flow('spike_simulation')

    return chip

def configure_verilator(hex_path, expect):
    # TODO: need to implement ['option', 'entrypoint'] - design name should be
    # consistent for keeping a full lifecycle manifest + future packaging plans.
    chip = make_chip(design='zverif_top')

    chip.set('option', 'jobname', 'verify')
    chip.set('option', 'flow', 'verilator_compilation')

    # Additional verification sources
    chip.add('input', 'verilog', glob.glob('verif/verilator/*.v'))
    chip.add('input', 'c', glob.glob('verif/verilator/*.cc'))

    # Tool configuration
    chip.set('tool', 'verilator', 'var', 'compile', '0', 'extraopts', ['--trace'])
    chip.set('tool', 'verilator_run', 'var', 'run', '0', '+firmware', hex_path)
    chip.set('tool', 'verilator_run', 'var', 'run', '0', 'expect', expect)

    return chip

def verify(tool='verilator', app='hello'):
    elf_path, hex_path, expect = build_app(app)

    if tool == 'verilator':
        chip = configure_verilator(elf_path, expect)
    elif tool == 'spike':
        chip = configure_spike(hex_path, expect)
    else:
        raise ValueError(f'Unsupported tool {tool} for target verify')

    return chip

def build():
    chip = make_chip()
    chip.set('option', 'jobname', 'rtl2gds')
    chip.set('option', 'flow', 'asicflow')

    return chip

def main():
    '''This is a rough sketch of what I think a nice SC build script CLI could
    look like.

    Features:
    - Ability to specify "target" that corresponds to a function in the file.
    - Ability to pass target-specific options along (e.g. which app to run in
    simulation).
    - Ability to pass through SC CLI options that are handy to tweak while
    debugging without modifying the script (e.g. -quiet, -steplist).
    - Support some set of handy/common debug tasks (e.g. dumping flowgraph)
    without modifying the script.

    I'm not set on the specific interface, but I think all these features are
    useful to have (I'd say the first two are mandatory). It would also be good
    to make sure there are nice help messages for each target/option.

    One open question: should the CLI go through `sc`, or be an API function
    (a-la `create_cmdline()`) that adds a standardized CLI to an existing
    script.

    E.g.:

    sc picorv32:verify --tool spike --app hello -- -quiet

    vs.

    ./picorv32.py verify --tool spike --app hello -- -quiet
    '''
    # TODO: How to specify targets in real CLI? Options:
    # - Explicit list, like here
    # - By Python reflection (common prefix? any public method?, predefined list?)
    targets = {
        'verify': verify,
        'build': build,
    }
    parser = argparse.ArgumentParser(description='PicoRV32 build script')
    subparsers = parser.add_subparsers(dest='target')

    for target, func in targets.items():
        subparser = subparsers.add_parser(target, help=f'Run {target}')
        args = inspect.getfullargspec(func).args
        for arg in args:
            subparser.add_argument(f'--{arg}',
                                   required=False,
                                   default=argparse.SUPPRESS)

        subparser.add_argument('--flowgraph',
                                action='store_true',
                                default=False,
                                help='Dump flowgraph instead of running build.')

        subparser.add_argument('sc options', nargs=argparse.REMAINDER)

    args = vars(parser.parse_args())

    # Default target
    # TODO: this breaks if default target has required args
    if args['target'] is None:
        target = 'build'
    else:
        target = args['target']

    target_func = targets[target]
    func_arg_names = inspect.getfullargspec(target_func).args
    func_args = {k:v for k, v in args.items() if k in func_arg_names}

    # A bit of a hack: filter out sys.argv into stuff that will get processed by
    # SC CLI (chip.create_cmdline())
    sys.argv = [sys.argv[0]] + args['sc options'][1:]

    chip = target_func(**func_args)

    if args['flowgraph']:
        jobname = chip.get('option', 'jobname')
        chip.write_flowgraph(f'{jobname}.png')
    else:
        chip.run()

if __name__ == '__main__':
    main()
