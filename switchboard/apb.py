# Python interface for AXI-Lite reads and writes

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from math import floor, ceil, log2
from numbers import Integral

from _switchboard import PySbPacket, PySbTx, PySbRx


class ApbTxRx:
    def __init__(
        self,
        uri: str,
        fresh: bool = True,
        data_width: int = 32,
        addr_width: int = 16,
        prot: int = 0,
        slv_err_expected: bool = False,
        queue_suffix: str = '.q',
        max_rate: float = -1
    ):
        """
        Parameters
        ----------
        uri: str
            Base name of for switchboard queues used to convey APB transactions.
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
        slv_err_expected: bool, optional
            Default response to expect from reads and writes.
            None means "don't check the response".
            This default can be overridden on a transaction-by-transaction basis.
        queue_suffix: str, optional
            File extension/suffix to use when naming switchboard queues that carry
            APB transactions.  For example, if set to ".queue", the write address
            queue name will be "{uri}-aw.queue"
        """

        # check data types
        assert isinstance(data_width, Integral), 'data_width must be an integer'
        assert isinstance(addr_width, Integral), 'addr_width must be an integer'

        # check that data width is a multiple of a byte
        data_width_choices = [8, 16, 32, 64, 128, 256, 512, 1024]
        assert data_width in data_width_choices, \
            f'data_width must be in {data_width_choices}'

        # check that data and address widths are supported
        SBDW = 416
        assert 0 < data_width <= floor(SBDW / (1 + (1 / 8))), 'data_width out of range'
        assert 0 < addr_width <= SBDW - 3, 'addr_width out of range'

        # save settings
        self.data_width = data_width
        self.addr_width = addr_width
        self.default_prot = prot
        self.default_slv_err_expected = slv_err_expected

        # create the queues
        self.apb_req = PySbTx(f'{uri}_apb_req{queue_suffix}', fresh=fresh, max_rate=max_rate)
        self.apb_resp = PySbRx(f'{uri}_apb_resp{queue_suffix}', fresh=fresh, max_rate=max_rate)

    @property
    def strb_width(self):
        return self.data_width // 8

    def write(
        self,
        addr: Integral,
        data,
        prot: Integral = None,
        slv_err_expected: bool = None
    ):
        """
        Parameters
        ----------
        addr: int
            Address to write to

        data: np.uint8, np.uint16, np.uint32, np.uint64, or np.array
            Data to write

        prot: Integral
            Value of PROT for this transaction.  Defaults to the value provided in the
            ApbTxRx constructor if not provided, which in turn defaults to 0.

        slv_err_expected: str, optional
            Response to expect for this transaction.
            None means, "don't check the response". Defaults to the
            value provided in the ApbTxRx constructor if not provided, which in turn
            defaults to False.

        Returns
        -------
        bool
            slv_err: True if SLVERR was received, False otherwise.
        """
        (rd_data, slv_err) = self.transaction(
            write=True,
            addr=addr,
            data=data,
            prot=prot,
            slv_err_expected=slv_err_expected
        )
        return slv_err

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
        (rd_data, slv_err) = self.transaction(
            write=False,
            addr=addr,
            data=None,
            prot=prot,
            slv_err_expected=resp_expected
        )
        return rd_data

    def transaction(
        self,
        write: bool,
        addr: Integral,
        data,
        prot: Integral = None,
        slv_err_expected: bool = None
    ):
        """
        Parameters
        ----------
        addr: int
            Address to write to

        data: np.uint8, np.uint16, np.uint32, np.uint64
            Data to write

        prot: Integral
            Value of PROT for this transaction.  Defaults to the value provided in the
            ApbTxRx constructor if not provided, which in turn defaults to 0.

        slv_err_expected: str, optional
            Response to expect for this transaction.
            None means, "don't check the response". Defaults to the
            value provided in the ApbTxRx constructor if not provided, which in turn
            defaults to False.

        Returns
        -------
        bool
            slv_err: True if SLVERR was received, False otherwise.
        """

        # set defaults

        if prot is None:
            prot = self.default_prot

        if slv_err_expected is None:
            slv_err_expected = self.default_slv_err_expected

        # check/standardize data types

        assert isinstance(addr, Integral), 'addr must be an integer'
        addr = int(addr)

        assert isinstance(prot, Integral), 'prot must be an integer'
        prot = int(prot)

        if data is None:
            data = np.zeros((self.data_width // 8,), dtype=np.uint8)
        elif isinstance(data, np.integer):
            data = np.frombuffer(data.tobytes(), dtype=np.uint8)
        else:
            raise TypeError(f"Unknown data type: {type(data)}")

        bytes_to_send = data.size

        # range validation

        assert 0 <= addr < (1 << self.addr_width), 'addr out of range'
        assert addr + bytes_to_send <= (1 << self.addr_width), \
            "transaction exceeds the address space."

        assert 0 <= prot < (1 << 3), 'prot out of range'

        header_bytes: int = int(ceil((1 + 3 + self.strb_width) / 8.0))
        data_bytes: int = self.data_width // 8
        addr_bytes: int = self.addr_width // 8

        addr_mask = (1 << self.addr_width) - 1
        addr_mask >>= ceil(log2(data_bytes))
        addr_mask <<= ceil(log2(data_bytes))

        # calculate strobe value based on the offset and number
        # of bytes that we're writing.
        strb = (1 << data_bytes) - 1
        header = int(write)
        header = (header << 3) | prot
        header = (header << self.strb_width) | strb
        header = np.frombuffer(
            header.to_bytes(header_bytes, 'little'),
            dtype=np.uint8
        )

        addr_as_buff = np.frombuffer(
            (addr & addr_mask).to_bytes((self.addr_width + 7) // 8, 'little'),
            dtype=np.uint8
        )

        pack = np.empty((header_bytes + addr_bytes + data_bytes,), dtype=np.uint8)
        pack[0:data_bytes] = data
        pack[data_bytes:data_bytes + addr_bytes] = addr_as_buff
        pack[data_bytes + addr_bytes:] = header
        pack = PySbPacket(data=pack, flags=1, destination=0)
        # Transmit request
        self.apb_req.send(pack, True)

        # wait for response
        pack = self.apb_resp.recv(True)
        pack = pack.data.tobytes()
        pack = int.from_bytes(pack, 'little')

        # decode the response
        rd_data = pack & ((1 << self.data_width) - 1)
        slv_err = bool((pack >> self.data_width) & 0b1)

        # check the response if desired
        if slv_err_expected is not None:
            assert slv_err == slv_err_expected, f'Unexpected response: slv_err = {slv_err}'

        return (rd_data, slv_err)


def apb_uris(prefix, suffix='.q'):
    # returns a list of the URIs associated with a given APB
    # prefix.  For example, apb_uris('apb') returns ['apb_apb_req.q',
    # 'apb_apb_resp.q'].  Changing the optional suffix
    # argument changes the file extension assumed in generating this list.

    return [
        f'{prefix}_apb_req{suffix}',
        f'{prefix}_apb_resp{suffix}'
    ]
