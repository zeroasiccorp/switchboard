#!/usr/bin/env python3

import time
from argparse import ArgumentParser
from pathlib import Path

from switchboard import delete_queue, binary_run, verilator_run, icarus_run

THIS_DIR = Path(__file__).resolve().parent


def main(mode="verilator"):
    # clean up old queues if present
    for q in ["client2rtl.q", "rtl2client.q"]:
        delete_queue(q)

    # start client and chip
    # this order yields a smaller waveform file
    client = binary_run(THIS_DIR / 'client')
    time.sleep(1)
    if mode == 'verilator':
        verilator_run(THIS_DIR / 'obj_dir' / 'Vtestbench', plusargs=['trace'])
    elif mode == 'icarus':
        icarus_run(THIS_DIR / 'testbench.vvp', modules=[THIS_DIR / 'switchboard_vpi.vpi'],
            extra_args=['-fst'])
    else:
        raise ValueError(f'Unknown mode: {mode}')

    # wait for client and chip to complete
    retcode = client.wait()
    assert retcode == 0


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('mode', default='verilator')
    args = parser.parse_args()

    main(mode=args.mode)
