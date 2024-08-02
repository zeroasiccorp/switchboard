#!/usr/bin/env python3

# Example illustrating how to interact with the umi_splitter module

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from switchboard import SbDut, random_umi_packet
from umi import sumi


def main():
    # build the simulator
    dut = build_testbench()

    # launch the simulation
    dut.simulate()

    umi_in = dut.intfs['umi_in']
    umi_out = [
        dut.intfs['umi_resp_out'],
        dut.intfs['umi_req_out']
    ]

    # main loop
    tx_rep = []
    tx_req = []
    n_sent = 0
    n_recv = 0

    while (n_sent < dut.args.n) or (n_recv < dut.args.n):
        # try to send a random packet
        if n_sent < dut.args.n:
            txp = random_umi_packet()
            if umi_in.send(txp, blocking=False):
                print('* IN *')
                print(str(txp))

                if (txp.cmd & 1) == 0:
                    # replies have the lsb of cmd set to "0"
                    tx_rep.append(txp)
                else:
                    # requests have the lsb of cmd set to "1"
                    tx_req.append(txp)

                n_sent += 1

        # try to receive from both outputs
        if n_recv < dut.args.n:
            for i, txq in enumerate([tx_rep, tx_req]):
                rxp = umi_out[i].recv(blocking=False)
                if rxp is not None:
                    print(f'* OUT #{i} *')
                    print(str(rxp))

                    assert txq[0] == rxp
                    txq.pop(0)

                    n_recv += 1


def build_testbench():
    dw = 256
    aw = 64
    cw = 32

    interfaces = {
        'umi_in': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='input'),
        'umi_resp_out': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output'),
        'umi_req_out': dict(type='umi', dw=dw, aw=aw, cw=cw, direction='output')
    }

    extra_args = {
        '-n': dict(type=int, default=3, help='Number of'
        ' transactions to send into the splitter during the test.')
    }

    dut = SbDut('umi_splitter', autowrap=True, cmdline=True, extra_args=extra_args,
        interfaces=interfaces, clocks=[])

    dut.use(sumi)

    dut.build()

    return dut


if __name__ == '__main__':
    main()
