# Loopback test to check the behavior of blocks that split/merge UMI packets

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from numbers import Integral
from typing import Iterable, Iterator, Union

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    tqdm = None

from .umi import UmiTxRx, random_umi_packet


def umi_loopback(
    umi: UmiTxRx,
    packets: Union[Integral, Iterable, Iterator] = 10,
    **kwargs
):
    """
    Performs a loopback test by sending packets into a block and checking that
    the packets received back are equivalent under the UMI split/merge rules.

    Parameters
    ----------
    umi: UmiTxRx
    packets:
        Can be a number, a list of packets, or a generator.

        - If this is a number, it represents the number of packets to send,
          which are generated with random_umi_packet. Any remaining arguments
          are passed directly to random_umi_packet.
        - If this is an iterable (list, tuple, etc.), then it represents a list
          of packets to use for the test.  This is helpful if you want to use a very
          specific sequence of transactions.
        - This can also be an iterator, which might be convenient if you want to
          send a very large number of packets without having to store them
          all in memory at once, e.g. (random_umi_packet() for _ in range(1000000))

    Raises
    ------
    ValueError
        If the number of packets is not positive or if the `packets` argument is empty
    Exception
        If a received packet does not match the corresponding transmitted packet

    """

    # input validation

    if isinstance(packets, Integral):
        if packets <= 0:
            raise ValueError(f'The number of packets must be positive (got packets={packets}).')
        else:
            total = packets
            packets = (random_umi_packet(**kwargs) for _ in range(packets))
    elif isinstance(packets, Iterable):
        if isinstance(packets, (list, tuple)):
            total = len(packets)
        else:
            total = float('inf')
        packets = iter(packets)
    elif isinstance(packets, Iterator):
        total = float('inf')
    else:
        raise TypeError(f'Unsupported type for packets: {type(packets)}')

    tx_sets = []  # kept for debug purposes
    tx_hist = []

    tx_set = None
    tx_partial = None

    rx_set = None  # kept for debug purposes
    rx_partial = None

    if tqdm is not None:
        pbar = tqdm(total=total)
    else:
        pbar = None

    # get the first element
    try:
        txp = next(packets)
        if pbar is not None:
            pbar.update(0)
    except StopIteration:
        raise ValueError('The argument "packets" is empty.')

    while (txp is not None) or (len(tx_hist) > 0):
        # send data
        if txp is not None:
            if umi.send(txp, blocking=False):
                if tx_partial is not None:
                    if not tx_partial.merge(txp):
                        tx_hist.append(tx_partial)
                        tx_sets.append(tx_set)
                        tx_start_new = True
                    else:
                        tx_set.append(txp)
                        tx_start_new = False
                else:
                    tx_start_new = True

                if tx_start_new:
                    tx_partial = txp
                    tx_set = [txp]

                try:
                    txp = next(packets)
                except StopIteration:
                    txp = None

                if txp is None:
                    # if this is the last packet, add it to the history
                    # even if the merge was successful
                    tx_hist.append(tx_partial)
                    tx_sets.append(tx_set)

        # receive data
        if len(tx_hist) > 0:
            rxp = umi.recv(blocking=False)
            if rxp is not None:
                # try to merge into an existing partial packet
                if rx_partial is not None:
                    if not rx_partial.merge(rxp):
                        print('=== Mismatch detected ===')
                        for i, p in enumerate(tx_sets[0]):
                            print(f'* TX[{i}] *')
                            print(p)
                        print('---')
                        for i, p in enumerate(rx_set):
                            print(f'* RX[{i}] *')
                            print(p)
                        print('=========================')
                        raise Exception('Mismatch!')
                    else:
                        rx_set.append(rxp)
                else:
                    rx_partial = rxp
                    rx_set = [rxp]

                # at this point it is guaranteed there is something in
                # rx_partial, so compare it to the expected outbound packet
                if rx_partial == tx_hist[0]:
                    tx_hist.pop(0)
                    tx_sets.pop(0)
                    rx_partial = None
                    rx_set = None

                    if pbar is not None:
                        pbar.update()

    if pbar is not None:
        pbar.close()
