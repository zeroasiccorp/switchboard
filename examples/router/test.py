#!/usr/bin/env python3

from pathlib import Path
from switchboard import switchboard, delete_queue, verilator_run, binary_run, SbDut

THIS_DIR = Path(__file__).resolve().parent


def main(aq="5555", bq="5556", cq="5557", dq="5558"):
    # build the simulator
    verilator_bin = build_testbench()

    # clean up old queues if present
    for q in [aq, bq, cq, dq]:
        delete_queue(f'queue-{q}')

    # start chip simulation
    verilator_run(verilator_bin)

    # start router
    start_router(aq=aq, bq=bq, cq=cq, dq=dq)

    # wait for client to complete
    client = binary_run(THIS_DIR / 'client')
    client.wait()


def start_router(aq, bq, cq, dq):
    args = []
    args += ['--tx', bq, cq]
    args += ['--rx', aq, dq]
    args += ['--route', '0:5556', '1:5557']

    return binary_run(bin=switchboard.path() / 'cpp' / 'router', args=args)


def build_testbench():
    dut = SbDut('testbench')

    EX_DIR = Path('..')

    # Set up inputs
    dut.input('testbench.sv')
    dut.input(EX_DIR / 'common' / 'verilator' / 'testbench.cc')

    # Settings
    dut.set('option', 'trace', True)  # enable VCD (TODO: FST option)

    # Build simulator
    dut.run()

    return dut.find_result('vexe', step='compile')


if __name__ == '__main__':
    main()
