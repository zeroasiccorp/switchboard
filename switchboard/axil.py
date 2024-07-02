# Python interface for AXI-Lite reads and writes

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from math import floor, ceil, log2
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
        queue_suffix: str = '.q',
        max_rate: float = -1
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
        self.default_resp_expected = resp_expected

        # create the queues
        self.aw = PySbTx(f'{uri}-aw{queue_suffix}', fresh=fresh, max_rate=max_rate)
        self.w = PySbTx(f'{uri}-w{queue_suffix}', fresh=fresh, max_rate=max_rate)
        self.b = PySbRx(f'{uri}-b{queue_suffix}', fresh=fresh, max_rate=max_rate)
        self.ar = PySbTx(f'{uri}-ar{queue_suffix}', fresh=fresh, max_rate=max_rate)
        self.r = PySbRx(f'{uri}-r{queue_suffix}', fresh=fresh, max_rate=max_rate)

    @property
    def strb_width(self):
        return self.data_width // 8

    def write(
        self,
        addr: Integral,
        data,
        prot: Integral = None,
        resp_expected: str = None
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
            AxiLiteTxRx constructor if not provided, which in turn defaults to 0.

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

        if prot is None:
            prot = self.default_prot

        if resp_expected is None:
            resp_expected = self.default_resp_expected

        # check/standardize data types

        assert isinstance(addr, Integral), 'addr must be an integer'
        addr = int(addr)

        assert isinstance(prot, Integral), 'prot must be an integer'
        prot = int(prot)

        if isinstance(data, np.ndarray):
            if data.ndim == 0:
                write_data = np.atleast_1d(data)
            elif data.ndim == 1:
                write_data = data
            else:
                raise ValueError(f'Can only write 1D arrays (got ndim={data.ndim})')

            if not np.issubdtype(write_data.dtype, np.integer):
                raise ValueError('Can only write integer dtypes such as uint8, uint16, etc.'
                    f'  (got dtype "{data.dtype}")')
        elif isinstance(data, np.integer):
            write_data = np.array(data, ndmin=1)
        else:
            raise TypeError(f"Unknown data type: {type(data)}")

        write_data = write_data.view(np.uint8)
        bytes_to_send = write_data.size

        # range validation

        assert 0 <= addr < (1 << self.addr_width), 'addr out of range'
        assert addr + bytes_to_send <= (1 << self.addr_width), \
            "transaction exceeds the address space."

        assert 0 <= prot < (1 << 3), 'prot out of range'

        # loop until all data is sent
        # TODO: move to C++?

        bytes_sent = 0

        data_bytes = self.data_width // 8
        strb_bytes = (self.strb_width + 7) // 8

        addr_mask = (1 << self.addr_width) - 1
        addr_mask >>= ceil(log2(data_bytes))
        addr_mask <<= ceil(log2(data_bytes))

        while bytes_sent < bytes_to_send:
            # find the offset into the data bus for this cycle.  bytes below
            # the offset will have write strobe de-asserted.
            offset = addr % data_bytes

            # determine how many bytes we're sending in this cycle
            bytes_this_cycle = min(bytes_to_send - bytes_sent, data_bytes - offset)

            # extract those bytes from the whole input data array, picking
            # up where we left off from the last iteration
            data_this_cycle = write_data[bytes_sent:bytes_sent + bytes_this_cycle]

            # calculate strobe value based on the offset and number
            # of bytes that we're writing.
            strb = ((1 << bytes_this_cycle) - 1) << offset
            strb = strb.to_bytes(strb_bytes, 'little')
            strb = np.frombuffer(strb, dtype=np.uint8)

            # transmit the write address
            pack = (prot << self.addr_width) | (addr & addr_mask)
            pack = pack.to_bytes((self.addr_width + 3 + 7) // 8, 'little')
            pack = np.frombuffer(pack, dtype=np.uint8)
            pack = PySbPacket(data=pack, flags=1, destination=0)
            self.aw.send(pack, True)

            # write data and strobe
            pack = np.empty((data_bytes + strb_bytes,), dtype=np.uint8)
            pack[offset:offset + bytes_this_cycle] = data_this_cycle
            pack[data_bytes:data_bytes + strb_bytes] = strb
            pack = PySbPacket(data=pack, flags=1, destination=0)
            self.w.send(pack, True)

            # wait for response
            pack = self.b.recv(True)
            pack = pack.data.tobytes()
            pack = int.from_bytes(pack, 'little')

            # decode the response
            resp = decode_resp(pack & 0b11)

            # check the response if desired
            if resp_expected is not None:
                assert resp.upper() == resp_expected.upper(), f'Unexpected response: {resp}'

            # increment pointers
            bytes_sent += bytes_this_cycle
            addr += bytes_this_cycle

        # return the last reponse
        return resp

    def read(
        self,
        addr: Integral,
        num_or_dtype,
        dtype=np.uint8,
        prot: Integral = None,
        resp_expected: str = None
    ):
        """
        Parameters
        ----------
        addr: int
            Address to read from

        num_or_dtype: int or numpy integer datatype
            If a plain int, `num_or_datatype` specifies the number of bytes to be read.
            If a numpy integer datatype (np.uint8, np.uint16, etc.), num_or_datatype
            specifies the data type to be returned.

        dtype: numpy integer datatype, optional
            If num_or_dtype is a plain integer, the value returned by this function
            will be a numpy array of type "dtype".  On the other hand, if num_or_dtype
            is a numpy datatype, the value returned will be a scalar of that datatype.

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

        # check/standardize data types

        assert isinstance(addr, Integral), 'addr must be an integer'
        addr = int(addr)

        assert isinstance(prot, Integral), 'prot must be an integer'
        prot = int(prot)

        if isinstance(num_or_dtype, (type, np.dtype)):
            bytes_to_read = np.dtype(num_or_dtype).itemsize
        else:
            bytes_to_read = num_or_dtype * np.dtype(dtype).itemsize

        # range validation

        assert 0 <= addr < (1 << self.addr_width), 'addr out of range'
        assert addr + bytes_to_read <= (1 << self.addr_width), \
            "transaction exceeds the address space."

        assert 0 <= prot < (1 << 3), 'prot out of range'

        # loop until all data is read
        # TODO: move to C++?

        bytes_read = 0
        data_bytes = self.data_width // 8

        addr_mask = (1 << self.addr_width) - 1
        addr_mask >>= ceil(log2(data_bytes))
        addr_mask <<= ceil(log2(data_bytes))

        retval = np.empty((bytes_to_read,), dtype=np.uint8)

        while bytes_read < bytes_to_read:
            # find the offset into the data bus for this cycle
            offset = addr % data_bytes

            # determine what data we're reading this cycle
            bytes_this_cycle = min(bytes_to_read - bytes_read, data_bytes - offset)

            # transmit read address
            pack = (prot << self.addr_width) | (addr & addr_mask)
            pack = pack.to_bytes((self.addr_width + 3 + 7) // 8, 'little')
            pack = np.frombuffer(pack, dtype=np.uint8)
            pack = PySbPacket(data=pack, flags=1, destination=0)
            self.ar.send(pack, True)

            # wait for response
            pack = self.r.recv(True)
            data = pack.data[offset:offset + bytes_this_cycle]
            resp = pack.data[data_bytes] & 0b11

            # check the reponse
            if resp_expected is not None:
                resp = decode_resp(resp)
                assert resp.upper() == resp_expected.upper(), f'Unexpected response: {resp}'

            # add this data to the return value
            retval[bytes_read:bytes_read + bytes_this_cycle] = data

            # increment pointers
            bytes_read += bytes_this_cycle
            addr += bytes_this_cycle

        if isinstance(num_or_dtype, (type, np.dtype)):
            return retval.view(num_or_dtype)[0]
        else:
            return retval.view(dtype)


def decode_resp(resp: Integral):
    assert isinstance(resp, Integral), 'response code must be an integer'
    assert 0 <= resp <= 3, 'response code out of range'

    return ['OKAY', 'EXOKAY', 'SLVERR', 'DECERR'][resp]
