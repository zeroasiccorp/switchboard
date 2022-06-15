from zverif.zvconfig import ZvConfig
from zverif.riscv import ZvRiscv
from zverif.spike import ZvSpike
from zverif.verilator import ZvVerilator

from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    add_spike(subparsers.add_parser('spike'))
    add_verilator(subparsers.add_parser('verilator'))
    add_sw(subparsers.add_parser('sw'))
    add_clean(subparsers.add_parser('clean'))

    args = parser.parse_args()
    args.func(args)

def add_spike(parser : ArgumentParser):
    parser.add_argument('mode', type=str,
        choices=['build', 'run', 'list', 'clean'])
    parser.add_argument('tests', type=str, nargs='*')
    parser.set_defaults(func=handle_spike_args)

def add_verilator(parser : ArgumentParser):
    parser.add_argument('mode', type=str,
        choices=['build', 'run', 'list', 'clean'])
    parser.add_argument('tests', type=str, nargs='*')
    parser.add_argument('--skip', type=str, nargs='+')
    parser.set_defaults(func=handle_verilator_args)

def add_sw(parser : ArgumentParser):
    parser.add_argument('mode', type=str,
        choices=['build', 'list', 'clean'])
    parser.add_argument('tests', type=str, nargs='*')
    parser.set_defaults(func=handle_sw_args)

def add_clean(parser : ArgumentParser):
    parser.set_defaults(func=handle_clean_args)

def handle_spike_args(args):
    cfg = ZvConfig()
    spike = ZvSpike(cfg)

    if args.mode == 'list':
        print(spike.list())
    elif args.mode == 'build':
        spike.build(args.tests)
    elif args.mode == 'run':
        spike.run(args.tests)
    elif args.mode == 'clean':
        spike.clean(args.tests)
    else:
        raise Exception(f'Unknown mode: {args.mode}')

def handle_verilator_args(args):
    cfg = ZvConfig()
    verilator = ZvVerilator(cfg)

    if args.mode == 'build':
        verilator.build()
    elif args.mode == 'run':
        verilator.run(args.tests, args.skip)
    elif args.mode == 'clean':
        verilator.clean()
    else:
        raise Exception(f'Unknown mode: {args.mode}')

def handle_sw_args(args):
    cfg = ZvConfig()
    sw = ZvRiscv(cfg)

    if args.mode == 'list':
        print(sw.list())
    elif args.mode == 'build':
        sw.build(args.tests)
    elif args.mode == 'clean':
        sw.clean(args.tests)
    else:
        raise Exception(f'Unknown mode: {args.mode}')

def handle_clean_args(args):
    pass

if __name__ == '__main__':
    main()