#!/usr/bin/env python3

# Example illustrating how UMI packets handled in the Switchboard Python binding
# Copyright (C) 2023 Zero ASIC

import numpy as np
from random import randint, choice
from switchboard import UmiTxRx, PyUmiPacket, delete_queue, verilator_run


def main(in_="in.q", out0="out0.q", out1="out1.q", n=3):
    # clean up old queues if present
    for q in [in_, out0, out1]:
        delete_queue(q)

    # launch the simulation
    verilator_run('obj_dir/Vtestbench', plusargs=['trace'])

    # instantiate TX and RX queues.  note that these can be instantiated without
    # specifying a URI, in which case the URI can be specified later via the
    # "init" method

    umi_in = UmiTxRx(in_, "")
    umi_out = [UmiTxRx("", out0), UmiTxRx("", out1)]

    tx_req_list = []
    tx_resp_list = []
    rx_list = [[], []]
    n_sent = 0
    n_recv = 0

    while (n_recv < n) or (n_sent < n):
        # send a packet with a certain probability
        if (n_sent < n):
            opcode = choice([0x2, 0x3])
            cmd = opcode | (1 << 22) | (1 << 23)
            dstaddr = randint(0, (1 << 64) - 1)
            srcaddr = randint(0, (1 << 64) - 1)
            data = np.random.randint(0, 256, (1,), dtype=np.uint8)

            txp = PyUmiPacket(cmd=cmd, dstaddr=dstaddr, srcaddr=srcaddr, data=data)
            if umi_in.send(txp, blocking=False):
                print('* IN *')
                print(str(txp))
                n_sent += 1
                if opcode == 0x2:
                    tx_resp_list.append(txp)
                else:
                    tx_req_list.append(txp)

        # receive a packet with a certain probability
        if (n_recv < n):
            for i in range(2):
                rxp = umi_out[i].recv(blocking=False)
                if rxp is not None:
                    print(f'* OUT #{i} *')
                    print(str(rxp))
                    rx_list[i].append(rxp)
                    n_recv += 1

    for list0, list1 in [[tx_resp_list, rx_list[0]], [tx_req_list, rx_list[1]]]:
        assert len(list0) == len(list1)
        for txp, rxp in zip(list0, list1):
            assert txp.cmd == rxp.cmd
            assert txp.dstaddr == rxp.dstaddr
            assert txp.srcaddr == rxp.srcaddr
            assert txp.data == rxp.data


if __name__ == '__main__':
    main()
