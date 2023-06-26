#!/usr/bin/env python3

import time

from pathlib import Path
from switchboard import delete_queue, verilator_run, binary_run

THIS_DIR = Path(__file__).resolve().parent


def main(rxq='rx.q', txq='tx.q'):
    # clean up old queues if present
    for q in [rxq, txq]:
        delete_queue(q)

    # start client and chip
    # this order yields a smaller VCD
    client = binary_run(THIS_DIR / 'client')
    time.sleep(1)
    chip = verilator_run('obj_dir/Vtestbench')

    # wait for client and chip to complete
    client.wait()
    chip.wait()


if __name__ == '__main__':
    main()
