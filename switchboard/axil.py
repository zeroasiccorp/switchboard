# Python interface for AXI-Lite reads and writes

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from math import floor
from numbers import Integral

from _switchboard import PySbPacket, PySbTx, PySbRx


class AxiLiteTxRx:
    def __init__(
        self,
        uri: str,
        fresh: bool = True,
        data_width: int = 32,
        addr_width: int = 16,
        prot: int = 0,
        resp_expected: str = 'OKAY',
        queue_suffix: str = '.q'
    ):
        """
        Parameters
        ----------
        uri: str
            Base name of for switchboard queues used to convey AXI transactions.  Five
            queues are used: write address (aw), write data (w), write response (b),
            read address (ar), and read response (r).  If the base name provided is
            "axil", the correponding queues will be "axil-aw.q", "axil-w.q", "axil-b.q",
            "axil-ar.q" and "axil-r.q".  The suffix used can be changed via the
            "queue_suffix" argument if needed.
        fresh: bool, optional
           If True (default), the queue specified by the uri parameter will get cleared
           before executing the simulation.
        data_width: int, optional
            Width the write and read data buses, in bits.
        addr_width: int, optional
            Width the write and read address buses, in bits.
        prot: int, optional
            Default value of PROT to use for read and write transactions.  Can be
            overridden on a transaction-by-transaction basis.
        resp_expected: str, optional
            Default response to expect from reads and writes.  Options are 'OKAY',
            'EXOKAY', 'SLVERR', 'DECERR'.  None means "don't check the response".
            This default can be overridden on a transaction-by-transaction basis.
        queue_suffix: str, optional
            File extension/suffix to use when naming switchboard queues that carry
            AXI transactions.  For example, if set to ".queue", the write address
            queue name will be "{uri}-aw.queue"
        """

        # check data types
        assert isinstance(data_width, Integral), 'data_width must be an integer'
        assert isinstance(addr_width, Integral), 'addr_width must be an integer'

        # check that data width is a multiple of a byte
        assert data_width % 8 == 0, 'data_width must be a multiple of 8'

        # check that data and address widths are supported
        SBDW = 416
        assert 0 < data_width <= floor(SBDW / (1 + (1 / 8))), 'data_width out of range'
        assert 0 < addr_width <= SBDW - 3, 'addr_width out of range'

        # save settings
        self.data_width = data_width
        self.addr_width = addr_width
        self.default_prot = prot
        self.default_resp_expected = resp_expected

        # create the queues
        self.aw = PySbTx(f'{uri}-aw{queue_suffix}', fresh=fresh)
        self.w = PySbTx(f'{uri}-w{queue_suffix}', fresh=fresh)
        self.b = PySbRx(f'{uri}-b{queue_suffix}', fresh=fresh)
        self.ar = PySbTx(f'{uri}-ar{queue_suffix}', fresh=fresh)
        self.r = PySbRx(f'{uri}-r{queue_suffix}', fresh=fresh)

    @property
    def strb_width(self):
        return self.data_width // 8

    def write(
        self,
        addr: Integral,
        data: Integral,
        prot: Integral = None,
        strb: Integral = None,
        resp_expected: str = None
    ):
        """
        Parameters
        ----------
        addr: int
            Address to write to

        data: Integral
            Data to write

        prot: Integral
            Value of PROT for this transaction.  Defaults to the value provided in the
            AxiLiteTxRx constructor if not provided, which in turn defaults to 0.

        strb: Integral
            Value of STRB for this transaction.  If not provided, defaults to a full-width
            write (i.e., all bits in STRB set to "1")

        resp_expected: str, optional
            Response to expect for this transaction.  Options are 'OKAY', 'EXOKAY', 'SLVERR',
            'DECERR', and None.  None means, "don't check the response". Defaults to the
            value provided in the AxiLiteTxRx constructor if not provided, which in turn
            defaults to 'OKAY'

        Returns
        -------
        str
            String representation of the response code, which may be 'OKAY', 'EXOKAY',
            'SLVERR', or 'DECERR'.
        """

        # set defaults

        if strb is None:
            strb = (1 << (self.data_width // 8)) - 1

        if prot is None:
            prot = self.default_prot

        if resp_expected is None:
            resp_expected = self.default_resp_expected

        # make sure everything is an int

        assert isinstance(addr, Integral), 'addr must be an integer'
        addr = int(addr)

        assert isinstance(data, Integral), 'data must be an integer'
        data = int(data)

        assert isinstance(prot, Integral), 'prot must be an integer'
        prot = int(prot)

        assert isinstance(strb, Integral), 'strb must be an integer'
        strb = int(strb)

        # range validation

        assert 0 <= addr < (1 << self.addr_width), 'addr out of range'
        assert 0 <= data < (1 << self.data_width), 'data out of range'
        assert 0 <= prot < (1 << 3), 'prot out of range'
        assert 0 <= strb < (1 << self.strb_width), 'strb out of range'

        # write address

        pack = (prot << self.addr_width) | addr
        pack = pack.to_bytes((self.addr_width + 3 + 7) // 8, 'little')
        pack = np.frombuffer(pack, dtype=np.uint8)
        pack = PySbPacket(data=pack, flags=1, destination=0)
        self.aw.send(pack)

        # write data

        pack = (strb << self.data_width) | data
        pack = pack.to_bytes((self.data_width + self.strb_width + 7) // 8, 'little')
        pack = np.frombuffer(pack, dtype=np.uint8)
        pack = PySbPacket(data=pack, flags=1, destination=0)
        self.w.send(pack)

        # wait for response
        pack = self.b.recv()
        pack = pack.data.tobytes()
        pack = int.from_bytes(pack, 'little')

        # decode the response
        resp = decode_resp(pack & 0b11)

        # check the response if desired
        if resp_expected is not None:
            assert resp.upper() == resp_expected.upper(), f'Unexpected response: {resp}'

        # return the reponse
        return resp

    def read(
        self,
        addr: Integral,
        prot: Integral = None,
        resp_expected: str = None
    ):
        """
        Parameters
        ----------
        addr: int
            Address to read from

        prot: Integral
            Value of PROT for this transaction.  Defaults to the value provided in the
            AxiLiteTxRx constructor if not provided, which in turn defaults to 0.

        resp_expected: str, optional
            Response to expect for this transaction.  Options are 'OKAY', 'EXOKAY', 'SLVERR',
            'DECERR', and None.  None means, "don't check the response". Defaults to the
            value provided in the AxiLiteTxRx constructor if not provided, which in turn
            defaults to 'OKAY'

        Returns
        -------
        int
            Value read, as an arbitrary-size Python integer.
        """

        # set defaults

        if prot is None:
            prot = self.default_prot

        if resp_expected is None:
            resp_expected = self.default_resp_expected

        # make sure everything is an int

        assert isinstance(addr, Integral), 'addr must be an integer'
        addr = int(addr)

        assert isinstance(prot, Integral), 'prot must be an integer'
        prot = int(prot)

        # range validation

        assert 0 <= addr < (1 << self.addr_width), 'addr out of range'
        assert 0 <= prot < (1 << 3), 'prot out of range'

        # read address
        pack = (prot << self.addr_width) | addr
        pack = pack.to_bytes((self.addr_width + 3 + 7) // 8, 'little')
        pack = np.frombuffer(pack, dtype=np.uint8)
        pack = PySbPacket(data=pack, flags=1, destination=0)
        self.ar.send(pack)

        # wait for response
        pack = self.r.recv()
        pack = pack.data.tobytes()
        pack = int.from_bytes(pack, 'little')

        # split apart the result into data and a response code
        data = pack & ((1 << self.data_width) - 1)
        resp = (pack >> self.data_width) & 0b11

        # check the reponse
        if resp_expected is not None:
            resp = decode_resp(resp)
            assert resp.upper() == resp_expected.upper(), f'Unexpected response: {resp}'

        return data


def decode_resp(resp: Integral):
    assert isinstance(resp, Integral), 'response code must be an integer'
    assert 0 <= resp <= 3, 'response code out of range'

    return ['OKAY', 'EXOKAY', 'SLVERR', 'DECERR'][resp]
