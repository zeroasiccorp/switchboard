# Python interface for AXI reads and writes

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import numpy as np

from math import floor, ceil, log2
from numbers import Integral

from _switchboard import PySbPacket, PySbTx, PySbRx


class AxiTxRx:
    def __init__(
        self,
        uri: str,
        fresh: bool = True,
        data_width: int = 32,
        addr_width: int = 16,
        id_width: int = 8,
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
            "axi", the correponding queues will be "axi-aw.q", "axi-w.q", "axi-b.q",
            "axi-ar.q" and "axi-r.q".  The suffix used can be changed via the
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
        self.id_width = id_width
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
        data,
        prot: Integral = None,
        burst: bool = True,
        resp_expected: str = None,
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
            AxiTxRx constructor if not provided, which in turn defaults to 0.

        resp_expected: str, optional
            Response to expect for this transaction.  Options are 'OKAY', 'EXOKAY', 'SLVERR',
            'DECERR', and None.  None means, "don't check the response". Defaults to the
            value provided in the AxiTxRx constructor if not provided, which in turn defaults
            to 'OKAY'

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
            write_data = np.array(data, ndmin=1, copy=False)
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
        data = np.empty((data_bytes,), dtype=np.uint8)

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
            data[offset:offset + bytes_this_cycle] = \
                write_data[bytes_sent:bytes_sent + bytes_this_cycle]

            # calculate strobe value based on the offset and number
            # of bytes that we're writing.
            strb = ((1 << bytes_this_cycle) - 1) << offset

            # transmit the write address
            self.aw.send(self.pack_addr(addr & addr_mask, prot=prot))

            # write data and strobe
            self.w.send(self.pack_w(data, strb=strb))

            # wait for response
            resp, id = self.unpack_b(self.b.recv())

            # decode the response
            resp = decode_resp(resp)

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
        burst: bool = True,
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
            AxiTxRx constructor if not provided, which in turn defaults to 0.

        resp_expected: str, optional
            Response to expect for this transaction.  Options are 'OKAY', 'EXOKAY', 'SLVERR',
            'DECERR', and None.  None means, "don't check the response". Defaults to the
            value provided in the AxiTxRx constructor if not provided, which in turn defaults
            to 'OKAY'

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
            self.ar.send(self.pack_addr(addr & addr_mask, prot=prot))

            # wait for response
            data, resp, id, last = self.unpack_r(self.r.recv())
            data = data[offset:offset + bytes_this_cycle]

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

    def pack_addr(self, addr, prot=0, id=0, len=0, size=0, burst=0b01, lock=0, cache=0):
        pack = 0

        # cache
        pack = (pack << 4) | (cache & 0b1111)

        # lock
        pack = (pack << 1) | (lock & 0b1)

        # burst
        pack = (pack << 2) | (burst & 0b11)

        # size
        pack = (pack << 3) | (size & 0b111)

        # len
        pack = (pack << 8) | (len & 0xff)

        # id
        pack = (pack << self.id_width) | (id & ((1 << self.id_width) - 1))

        # prot
        pack = (pack << 3) | (prot & 0b111)

        # addr
        pack = (pack << self.addr_width) | (addr & ((1 << self.addr_width) - 1))

        # convert to byte array
        pack = pack.to_bytes(
            (self.addr_width + 3 + self.id_width + 8 + 3 + 2 + 1 + 4 + 7) // 8,
            'little'
        )

        # convert to a numpy array
        pack = np.frombuffer(pack, dtype=np.uint8)

        # convert to an SB packet
        pack = PySbPacket(data=pack, flags=1, destination=0)

        return pack

    def pack_w(self, data, strb=None, last=1):
        if strb is None:
            strb = (1 << self.strb_width) - 1

        # pack non-data signals together
        rest = 0
        rest = (rest << 1) | (last & 1)
        rest = (rest << self.strb_width) | (strb & ((1 << self.strb_width) - 1))
        rest = rest.to_bytes(rest, 'little')
        rest = np.frombuffer(rest, dtype=np.uint8)

        # figure out how many bytes the data + rest of the signals take up
        data_bytes = self.data_width // 8
        rest_bytes = (self.strb_width + 1 + 7) // 8

        # pack everything together in a numpy array
        pack = np.empty((data_bytes + rest_bytes,), dtype=np.uint8)
        pack[:data_bytes] = data
        pack[data_bytes:] = strb

        # convert to an SB packet
        pack = PySbPacket(data=pack, flags=1, destination=0)

        return pack

    def unpack_b(self, pack):
        pack = pack.data.tobytes()
        pack = int.from_bytes(pack, 'little')

        # resp
        resp = pack & 0b11
        pack >>= 2

        # id
        id = pack & ((1 << self.id_width) - 1)
        pack >>= self.id_width

        return resp, id

    def unpack_r(self, pack):
        data_bytes = self.data_width // 8

        data = pack.data[:data_bytes]
        rest = pack.data[data_bytes:]

        rest = rest.tobytes()
        rest = int.from_bytes(rest, 'little')

        # resp
        resp = rest & 0b11
        rest >>= 2

        # id
        id = rest & ((1 << self.id_width) - 1)
        rest >>= self.id_width

        # last
        last = rest & 0b1
        rest >>= 1

        return data, resp, id, last


def decode_resp(resp: Integral):
    assert isinstance(resp, Integral), 'response code must be an integer'
    assert 0 <= resp <= 3, 'response code out of range'

    return ['OKAY', 'EXOKAY', 'SLVERR', 'DECERR'][resp]
