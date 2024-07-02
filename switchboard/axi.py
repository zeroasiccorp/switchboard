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
        id: int = 0,
        size: int = None,
        max_beats: int = 256,
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
            "axi", the correponding queues will be "axi-aw.q", "axi-w.q", "axi-b.q",
            "axi-ar.q" and "axi-r.q".  The suffix used can be changed via the
            "queue_suffix" argument if needed.
        fresh: bool, optional
           If True (default), the queue specified by the uri parameter will get cleared
           before executing the simulation.
        data_width: int, optional
            Width of the write and read data buses, in bits.
        addr_width: int, optional
            Width of the write and read address buses, in bits.
        addr_width: int, optional
            Width of the write and read IDs, in bits.
        prot: int, optional
            Default value of PROT to use for read and write transactions.  Can be
            overridden on a transaction-by-transaction basis.
        id: int, option
            Default ID to use for read/write transactions.
        size: int, optional
            AXI SIZE indicating the default width of read/write transactions.  This can
            be overridden on a transaction-by-transaction basis via the "size" argument.
            If a value isn't provided here, the default size is set to the full data bus
            width.
        max_beats: int, optional
            Maximum number of beats in a single AXI transaction.  Defaults to 256; set to
            1 to disable bursting.  Set to 16 for AXI3 compatibility.
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

        # determine default size
        if size is None:
            size = ceil(log2(data_width // 8))

        # save settings
        self.data_width = data_width
        self.addr_width = addr_width
        self.id_width = id_width
        self.default_prot = prot
        self.default_id = id
        self.default_size = size
        self.default_max_beats = max_beats
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
        id: Integral = None,
        size: Integral = None,
        max_beats: Integral = None,
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
            AxiTxRx constructor if not provided, which in turn defaults to 0.

        id: int, option
            ID to use for write transactions.  If not provided, defaults to the value
            given in the constructor, which in turn defaults to 0.

        size: int, optional
            AXI SIZE indicating the width of write transactions.  If not provided, defaults
            to the value given in the constructor, which in turn defaults to the full
            data bus width.

        max_beats: int, optional
            Maximum number of beats in a single write transaction.  If not provided, defaults
            to the value given in the constructor, which in turn defaults to 256.

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

        if id is None:
            id = self.default_id

        if size is None:
            size = self.default_size

        if max_beats is None:
            max_beats = self.default_max_beats

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
        data = np.empty((data_bytes,), dtype=np.uint8)

        addr_mask = (1 << self.addr_width) - 1
        addr_mask >>= size
        addr_mask <<= size

        mask_4k = (1 << self.addr_width) - 1
        mask_4k >>= 12
        mask_4k <<= 12

        increment_4k = 1 << 12

        while bytes_sent < bytes_to_send:
            top_addr = addr + (bytes_to_send - bytes_sent) - 1

            # limit transfer to the longest burst possible
            longest_burst = max_beats * (1 << size)
            top_addr = min(top_addr, (addr & addr_mask) + longest_burst - 1)

            # don't cross a 4k boundary
            next_4k_boundary = (addr & mask_4k) + increment_4k - 1
            top_addr = min(top_addr, next_4k_boundary)

            # calculate the number of beats
            beats = ceil((top_addr - (addr & addr_mask) + 1) / (1 << size))

            assert 1 <= beats <= max_beats

            # transmit the write address
            self.aw.send(self.pack_addr(addr & addr_mask, prot=prot, size=size,
                len=beats - 1, id=id), True)

            for beat in range(beats):
                # find the offset into the data bus for this beat.  bytes below
                # the offset will have write strobe de-asserted.
                offset = addr - (addr & addr_mask)

                # determine how many bytes we're sending in this cycle
                bytes_this_beat = min(bytes_to_send - bytes_sent, (1 << size) - offset)

                # extract those bytes from the whole input data array, picking
                # up where we left off from the last beat
                data[offset:offset + bytes_this_beat] = \
                    write_data[bytes_sent:bytes_sent + bytes_this_beat]

                # calculate strobe value based on the offset and number
                # of bytes that we're writing.
                strb = ((1 << bytes_this_beat) - 1) << offset

                # write data and strobe
                if beat == beats - 1:
                    last = 1
                else:
                    last = 0
                self.w.send(self.pack_w(data, strb=strb, last=last), True)

                # increment pointers
                bytes_sent += bytes_this_beat
                addr += bytes_this_beat

            # wait for response
            resp, id = self.unpack_b(self.b.recv(True))

            # decode the response
            resp = decode_resp(resp)

            # check the response if desired
            if resp_expected is not None:
                assert resp.upper() == resp_expected.upper(), f'Unexpected response: {resp}'

        # return the last reponse
        return resp

    def read(
        self,
        addr: Integral,
        num_or_dtype,
        dtype=np.uint8,
        prot: Integral = None,
        id: Integral = None,
        size: Integral = None,
        max_beats: Integral = None,
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

        id: int, option
            ID to use for read transactions.  If not provided, defaults to the value
            given in the constructor, which in turn defaults to 0.

        size: int, optional
            AXI SIZE indicating the width of read transactions.  If not provided, defaults
            to the value given in the constructor, which in turn defaults to the full
            data bus width.

        max_beats: int, optional
            Maximum number of beats in a single read transaction.  If not provided, defaults
            to the value given in the constructor, which in turn defaults to 256.

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

        if id is None:
            id = self.default_id

        if size is None:
            size = self.default_size

        if max_beats is None:
            max_beats = self.default_max_beats

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

        addr_mask = (1 << self.addr_width) - 1
        addr_mask >>= size
        addr_mask <<= size

        mask_4k = (1 << self.addr_width) - 1
        mask_4k >>= 12
        mask_4k <<= 12

        increment_4k = 1 << 12

        retval = np.empty((bytes_to_read,), dtype=np.uint8)

        while bytes_read < bytes_to_read:
            top_addr = addr + (bytes_to_read - bytes_read) - 1

            # limit transfer to the longest burst possible
            longest_burst = max_beats * (1 << size)
            top_addr = min(top_addr, (addr & addr_mask) + longest_burst - 1)

            # don't cross a 4k boundary
            next_4k_boundary = (addr & mask_4k) + increment_4k - 1
            top_addr = min(top_addr, next_4k_boundary)

            # calculate the number of beats
            beats = ceil((top_addr - (addr & addr_mask) + 1) / (1 << size))
            assert 1 <= beats <= max_beats

            # transmit read address
            self.ar.send(self.pack_addr(addr & addr_mask, prot=prot, size=size,
                len=beats - 1, id=id), True)

            for _ in range(beats):
                # find the offset into the data bus for this beat.  bytes below
                # the offset will have write strobe de-asserted.
                offset = addr - (addr & addr_mask)

                # determine how many bytes we're sending in this cycle
                bytes_this_beat = min(bytes_to_read - bytes_read, (1 << size) - offset)

                # wait for response
                data, resp, id, last = self.unpack_r(self.r.recv(True))
                retval[bytes_read:bytes_read + bytes_this_beat] = \
                    data = data[offset:offset + bytes_this_beat]

                # check the reponse
                if resp_expected is not None:
                    resp = decode_resp(resp)
                    assert resp.upper() == resp_expected.upper(), f'Unexpected response: {resp}'

                # increment pointers
                bytes_read += bytes_this_beat
                addr += bytes_this_beat

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

        # figure out how many bytes the data + rest of the signals take up
        data_bytes = self.data_width // 8
        rest_bytes = (self.strb_width + 1 + 7) // 8

        # pack non-data signals together
        rest = 0
        rest = (rest << 1) | (last & 1)
        rest = (rest << self.strb_width) | (strb & ((1 << self.strb_width) - 1))
        rest = rest.to_bytes(rest_bytes, 'little')
        rest = np.frombuffer(rest, dtype=np.uint8)

        # pack everything together in a numpy array
        pack = np.empty((data_bytes + rest_bytes,), dtype=np.uint8)
        pack[:data_bytes] = data
        pack[data_bytes:] = rest

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


def axi_uris(prefix, suffix='.q'):
    # returns a list of the URIs associated with a given AXI or AXI-Lite
    # prefix.  For example, axi_uris('axi') returns ['axi-aw.q', 'axi-w.q',
    # 'axi-b.q', 'axi-ar.q', 'axi-r.q'].  Changing the optional suffix
    # argument changes the file extension assumed in generating this list.

    return [
        f'{prefix}-aw{suffix}',
        f'{prefix}-w{suffix}',
        f'{prefix}-b{suffix}',
        f'{prefix}-ar{suffix}',
        f'{prefix}-r{suffix}'
    ]
