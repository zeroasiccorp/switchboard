# Python interface for AXI-Lite reads and writes

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from _switchboard import PySbPacket, PySbTx, PySbRx


class AxiLiteTxRx:
    def __init__(
        self,
        uri: str,
        fresh: bool = True,
        data_width: int = 32,
        addr_width: int = 16
    ):
        # validate input
        assert data_width <= 64, 'Data width currently limited to 64 bits'
        assert addr_width <= 64, 'Address width currently limited to 64 bits'

        # save settings
        self.data_width = data_width
        self.addr_width = addr_width

        # create the queues
        self.aw = PySbTx(f'{uri}-aw.q', fresh=fresh)
        self.w = PySbTx(f'{uri}-w.q', fresh=fresh)
        self.b = PySbRx(f'{uri}-b.q', fresh=fresh)
        self.ar = PySbTx(f'{uri}-ar.q', fresh=fresh)
        self.r = PySbRx(f'{uri}-r.q', fresh=fresh)

    def write(self, addr, data, prot=0, strb=None):
        # set defaults
        if strb is None:
            strb = (1 << self.data_width) - 1

        # write address
        addr = np.array([addr], dtype=get_np_dtype(self.addr_width)).view(np.uint8)
        addr = np.concatenate((addr, np.array([prot], dtype=np.uint8)))
        pack = PySbPacket(data=addr, flags=1, destination=0)
        self.aw.send(pack)

        # write data
        data = np.array([data], dtype=get_np_dtype(self.data_width)).view(np.uint8)
        data = np.concatenate((data, np.array([strb], dtype=np.uint8)))
        pack = PySbPacket(data=data, flags=1, destination=0)
        self.w.send(pack)

        # wait for response
        self.b.recv()

    def read(self, addr, prot=0):
        # read address
        addr = np.array([addr], dtype=get_np_dtype(self.addr_width)).view(np.uint8)
        addr = np.concatenate((addr, np.array([prot], dtype=np.uint8)))
        pack = PySbPacket(data=addr, flags=1, destination=0)
        self.ar.send(pack)

        # read data
        pack = self.r.recv()
        return pack.data.view(get_np_dtype(self.data_width))[0]


def get_np_dtype(width):
    import numpy as np

    if width == 8:
        return np.uint8
    elif width == 16:
        return np.uint16
    elif width == 32:
        return np.uint32
    elif width == 64:
        return np.uint64
    else:
        raise ValueError(f'Unsupported width: {width}')
