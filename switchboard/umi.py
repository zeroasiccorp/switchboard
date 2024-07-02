# Python interface for UMI reads, writes, and atomic operations

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import random
import numpy as np

from numbers import Integral
from typing import Iterable, Union, Dict

from _switchboard import (PyUmi, PyUmiPacket, umi_pack, UmiCmd, UmiAtomic)
from .gpio import UmiGpio

# note: it was convenient to implement some of this in Python, rather
# than have everything in C++, because it was easier to provide
# flexibility with numpy types


class UmiTxRx:
    def __init__(self, tx_uri: str = None, rx_uri: str = None,
        srcaddr: Union[int, Dict[str, int]] = 0, posted: bool = False,
        max_bytes: int = None, fresh: bool = False, error: bool = True,
        max_rate: float = -1):
        """
        Parameters
        ----------
        tx_uri: str, optional
            Name of the switchboard queue that
            write() and send() will send UMI packets to.  Defaults to
            None, meaning "unused".
        rx_uri: str, optional
            Name of the switchboard queue that
            read() and recv() will receive UMI packets from.  Defaults
            to None, meaning "unused".
        srcaddr: int, optional
            Default srcaddr to use for reads,
            ack'd writes, and atomics.  Defaults to 0.  Can also be
            provided as a dictionary with separate defaults for each
            type of transaction: srcaddr={'read': 0x1234, 'write':
            0x2345, 'atomic': 0x3456}.  When the defaults are provided
            with a dictionary, all keys are optional.  Transactions
            that are not specified in the dictionary will default
            to a srcaddr of 0.
        posted: bool, optional
            If True, default to using posted
            (i.e., non-ack'd) writes.  This can be overridden on a
            transaction-by-transaction basis.  Defaults to False.
        max_bytes: int, optional
            Default maximum number of bytes
            to use in each UMI transaction.  Can be overridden on a
            transaction-by-transaction basis.  Defaults to 32 bytes.
        fresh: bool, optional
           If True, the queue specified by the uri parameter will get
           cleared before executing the simulation.
        error: bool, optional
            If True, error out upon receiving an unexpected UMI response.
        """

        if tx_uri is None:
            tx_uri = ""

        if rx_uri is None:
            rx_uri = ""

        self.umi = PyUmi(tx_uri, rx_uri, fresh, max_rate=max_rate)

        if srcaddr is not None:
            # convert srcaddr default to a dictionary if necessary
            if isinstance(srcaddr, int):
                srcaddr = {
                    'read': srcaddr,
                    'write': srcaddr,
                    'atomic': srcaddr
                }

            if isinstance(srcaddr, dict):
                self.def_read_srcaddr = int(srcaddr.get('read', 0))
                self.def_write_srcaddr = int(srcaddr.get('write', 0))
                self.def_atomic_srcaddr = int(srcaddr.get('atomic', 0))
            else:
                raise ValueError(f'Unsupported default srcaddr specification: {srcaddr}')
        else:
            raise ValueError('Default value of "srcaddr" cannot be None.')

        if posted is not None:
            self.default_posted = bool(posted)
        else:
            raise ValueError('Default value of "posted" cannot be None.')

        if max_bytes is None:
            max_bytes = 32

        self.default_max_bytes = max_bytes
        self.default_error = error

    def gpio(
        self,
        iwidth: int = 32,
        owidth: int = 32,
        init: int = 0,
        dstaddr: int = 0,
        srcaddr: int = 0,
        posted: bool = False,
        max_bytes: int = 32
    ) -> UmiGpio:
        """
        Returns an object for communicating with umi_gpio modules.

        Parameters
        ----------
        iwidth: int
            Width of GPIO input (bits). Defaults to 32.
        owidth: int
            Width of GPIO output (bits). Defaults to 32.
        init: int
            Default value of GPIO output. Defaults to 0.
        dstaddr: int
            Base address of the GPIO device. Defaults to 0.
        srcaddr: int
            Source address to which responses should be routed. Defaults to 0.
        posted: bool
            Whether writes should be sent as posted. Defaults to False.
        max_bytes: int
            Maximum number of bytes in a single transaction to umi_gpio.

        Returns
        -------
        UmiGpio
            UmiGpio object with .i (input) and .o (output) attributes
        """

        return UmiGpio(
            iwidth=iwidth,
            owidth=owidth,
            init=init,
            dstaddr=dstaddr,
            srcaddr=srcaddr,
            posted=posted,
            max_bytes=max_bytes,
            umi=self
        )

    def init_queues(self, tx_uri: str = None, rx_uri: str = None, fresh: bool = False):
        """
        Parameters
        ----------
        tx_uri: str, optional
            Name of the switchboard queue that
            write() and send() will send UMI packets to.  Defaults to
            None, meaning "unused".
        rx_uri: str, optional
            Name of the switchboard queue that
            read() and recv() will receive UMI packets from.  Defaults
            to None, meaning "unused".
        fresh: bool, optional
           If True, the queue specified by the uri parameter will get
           cleared before executing the simulation.
        """

        if tx_uri is None:
            tx_uri = ""

        if rx_uri is None:
            rx_uri = ""

        self.umi.init(tx_uri, rx_uri, fresh)

    def send(self, p, blocking=True) -> bool:
        """
        Sends (or tries to send if burst=False) a UMI transaction (PyUmiPacket)
        Returns True if the packet was sent successfully, else False.

        Parameters
        ----------
        p: PyUmiPacket
            The UMI packet that will be sent
        blocking: bool, optional
            If True, the program will pause execution until a response to the write request
            is received.

        Returns
        -------
        bool
            Returns true if the `p` was sent successfully
        """

        return self.umi.send(p, blocking)

    def recv(self, blocking=True) -> PyUmiPacket:
        """
        Wait for and return a UMI packet if blocking=True, otherwise return a
        UMI packet if one can be read immediately, and None otherwise.

        Parameters
        ----------
        blocking: bool, optional
            If True, the function will wait until a UMI packet can be read.
            If False, a None type will be returned if no UMI packet can be read
            immediately.

        Returns
        -------
        PyUmiPacket
            If `blocking` is True, a PyUmiPacket is always returned. If `blocking` is
            False, a PyUmiPacket object will be returned if one can be read immediately.
            Otherwise, a None type will be returned.
        """

        return self.umi.recv(blocking)

    def write(self, addr, data, srcaddr=None, max_bytes=None,
        posted=None, qos=0, prot=0, progressbar=False, check_alignment=True,
        error=None):
        """
        Writes the provided data to the given 64-bit address.

        Parameters
        ----------
        addr: int
            64-bit address that will be written to

        data: np.uint8, np.uint16, np.uint32, np.uint64, or np.array
            Can be either a numpy integer type (e.g., np.uint32) or an numpy
            array of integer types (np.uint8, np.uin16, np.uint32, np.uint64, etc.).
            The `data` input may contain more than "max_bytes", in which case
            the write will automatically be split into multiple transactions.

        srcaddr: int, optional
            UMI source address used for the write transaction. This is sometimes needed to make
            the write response gets routed to the right place.

        max_bytes: int, optional
            Indicates the maximum number of bytes that can be used for any individual UMI
            transaction. If not specified, this defaults to the value of `max_bytes`
            provided in the UmiTxRx constructor, which in turn defaults to 32.

        posted: bool, optional
            If True, a write response will be received.

        qos: int, optional
            4-bit Quality of Service field in UMI Command

        prot: int, optional
            2-bit protection mode field in UMI command

        progressbar: bool, optional
            If True, the number of packets written will be displayed via a progressbar
            in the terminal.

        check_alignment: bool, optional
            If true, an exception will be raised if the `addr` parameter cannot be aligned based
            on the size of the `data` parameter

        error: bool, optional
            If True, error out upon receiving an unexpected UMI response.
        """

        # set defaults

        if max_bytes is None:
            max_bytes = self.default_max_bytes

        max_bytes = int(max_bytes)

        if srcaddr is None:
            srcaddr = self.def_write_srcaddr

        srcaddr = int(srcaddr)

        if posted is None:
            posted = self.default_posted

        posted = bool(posted)

        if error is None:
            error = self.default_error

        error = bool(error)

        # format the data to be written

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

        if check_alignment:
            size = dtype2size(write_data.dtype)
            if not addr_aligned(addr=addr, align=size):
                raise ValueError(f'addr=0x{addr:x} misaligned for size={size}')

        # perform write
        self.umi.write(addr, write_data, srcaddr, max_bytes,
            posted, qos, prot, progressbar, error)

    def write_readback(self, addr, value, mask=None, srcaddr=None, dtype=None,
        posted=True, write_srcaddr=None, check_alignment=True, error=None):
        """
        Writes the provided value to the given 64-bit address, and blocks
        until that value is read back from the provided address.

        Parameters
        ----------
        addr: int
            The destination address to write to and read from

        value: int, np.uint8, np.uint16, np.uint32, or np.uint64
            The data written to `addr`

        mask: int, optional
            argument (optional) allows the user to mask off some bits
            in the comparison of the data written vs. data read back.  For example,
            if a user only cares that bit "5" is written to "1", and does not care
            about the value of other bits read back, they could use mask=1<<5.

        srcaddr: int, optional
            The UMI source address used for the read transaction.  This is
            sometimes needed to make sure that reads get routed to the right place.

        dtype: np.uint8, np.uint16, np.uint32, or np.uint64, optional
            If `value` is specified as plain integer, then dtype must be specified,
            indicating a particular numpy integer type. This is so that the size of
            the UMI transaction can be set appropriately.

        posted: bool, optional
            By default, the write is performed as a posted write, however it is
            is possible to use an ack'd write by setting posted=False.

        write_srcaddr: int, optional
            If `posted`=True, write_srcaddr specifies the srcaddr used for that
            transaction. If write_srcaddr is None, the default srcaddr for writes
            will be used.

        check_alignment: bool, optional
            If true, an exception will be raised if the `addr` parameter cannot be aligned based
            on the size of the `data` parameter

        error: bool, optional
            If True, error out upon receiving an unexpected UMI response.

        Raises
        ------
        TypeError
            If `value` is not an integer type, if `mask` is not an integer type
        """

        # set defaults

        if srcaddr is None:
            srcaddr = self.def_read_srcaddr

        srcaddr = int(srcaddr)

        if write_srcaddr is None:
            write_srcaddr = self.def_write_srcaddr

        write_srcaddr = int(write_srcaddr)

        # convert value to a numpy datatype if it is not already
        if not isinstance(value, np.integer):
            if dtype is not None:
                value = dtype(value)
            else:
                raise TypeError("Must provide value as a numpy integer type, or specify dtype.")

        # set the mask to all ones if it is None
        if mask is None:
            nbits = (np.dtype(value.dtype).itemsize * 8)
            mask = (1 << nbits) - 1

        # convert mask to a numpy datatype if it is not already
        if not isinstance(mask, np.integer):
            if dtype is not None:
                mask = dtype(mask)
            else:
                raise TypeError("Must provide mask as a numpy integer type, or specify dtype.")

        # write, then read repeatedly until the value written is observed
        self.write(addr, value, srcaddr=write_srcaddr, posted=posted,
            check_alignment=check_alignment, error=error)
        rdval = self.read(addr, value.dtype, srcaddr=srcaddr,
            check_alignment=check_alignment, error=error)
        while ((rdval & mask) != (value & mask)):
            rdval = self.read(addr, value.dtype, srcaddr=srcaddr,
                check_alignment=check_alignment, error=error)

    def read(self, addr, num_or_dtype, dtype=np.uint8, srcaddr=None,
        max_bytes=None, qos=0, prot=0, check_alignment=True, error=None):
        """
        Parameters
        ----------
        addr: int
            The 64-bit address read from

        num_or_dtype: int or numpy integer datatype
            If a plain int, `num_or_datatype` specifies the number of bytes to be read.
            If a numpy integer datatype (np.uint8, np.uint16, etc.), num_or_datatype
            specifies the data type to be returned.

        dtype: numpy integer datatype, optional
            If num_or_dtype is a plain integer, the value returned by this function
            will be a numpy array of type "dtype".  On the other hand, if num_or_dtype
            is a numpy datatype, the value returned will be a scalar of that datatype.

        srcaddr: int, optional
           The UMI source address used for the read transaction.  This
           is sometimes needed to make sure that reads get routed to the right place.

        max_bytes: int, optional
            Indicates the maximum number of bytes that can be used for any individual UMI
            transaction. If not specified, this defaults to the value of `max_bytes`
            provided in the UmiTxRx constructor, which in turn defaults to 32.

        qos: int, optional
            4-bit Quality of Service field used in the UMI command

        prot: int, optional
            2-bit Protection mode field used in the UMI command

        error: bool, optional
            If True, error out upon receiving an unexpected UMI response.

        Returns
        -------
        numpy integer array
            An array of `num_or_dtype` bytes read from `addr`. The array will have the type
            specified by `dtype` or `num_or_dtype`
        """

        # set defaults

        if max_bytes is None:
            max_bytes = self.default_max_bytes

        max_bytes = int(max_bytes)

        if srcaddr is None:
            srcaddr = self.def_read_srcaddr

        srcaddr = int(srcaddr)

        if error is None:
            error = self.default_error

        error = bool(error)

        if isinstance(num_or_dtype, (type, np.dtype)):
            num = 1
            bytes_per_elem = np.dtype(num_or_dtype).itemsize
        else:
            num = num_or_dtype
            bytes_per_elem = np.dtype(dtype).itemsize

        if check_alignment:
            size = nbytes2size(bytes_per_elem)
            if not addr_aligned(addr=addr, align=size):
                raise ValueError(f'addr=0x{addr:x} misaligned for size={size}')

        result = self.umi.read(addr, num, bytes_per_elem, srcaddr, max_bytes,
            qos, prot, error)

        if isinstance(num_or_dtype, (type, np.dtype)):
            return result.view(num_or_dtype)[0]
        else:
            return result

    def atomic(self, addr, data, opcode, srcaddr=None, qos=0, prot=0, error=None):
        """
        Parameters
        ----------
        addr: int
            64-bit address atomic operation will be applied to.

        data: np.uint8, np.uint16, np.uint32, np.uint64
            must so that the size of the atomic operation can be determined.

        opcode: str or switchboard.UmiAtomic value
            Supported string values are 'add', 'and', 'or', 'xor', 'max', 'min',
            'minu', 'maxu', and 'swap' (case-insensitive).

        srcaddr: int, optional
            The UMI source address used for the atomic transaction.  This
            is sometimes needed to make sure the response get routed to the right place.

        qos: int, optional
            4-bit Quality of Service field used in the UMI command

        prot: int, optional
            2-bit Protection mode field used in the UMI command

        error: bool, optional
            If True, error out upon receiving an unexpected UMI response.

        Raises
        ------
        TypeError
            If `value` is not a numpy integer datatype

        Returns
        -------
        np.uint8, np.uint16, np.uint32, np.uint64
            The value returned by this function is the original value at addr,
            immediately before the atomic operation is applied.  The numpy dtype of the
            returned value will be the same as for "data".
        """

        # set defaults

        if srcaddr is None:
            srcaddr = self.def_atomic_srcaddr

        srcaddr = int(srcaddr)

        if error is None:
            error = self.default_error

        error = bool(error)

        # resolve the opcode to an enum if needed
        if isinstance(opcode, str):
            opcode = getattr(UmiAtomic, f'UMI_REQ_ATOMIC{opcode.upper()}')

        # format the data for sending
        if isinstance(data, np.integer):
            atomic_data = np.array(data, ndmin=1).view(np.uint8)
            result = self.umi.atomic(addr, atomic_data, opcode, srcaddr, qos, prot, error)
            return result.view(data.dtype)[0]
        else:
            raise TypeError("The data provided to atomic should be of a numpy integer type"
                " so that the transaction size can be determined")


def size2dtype(size: int, signed: bool = False, float: bool = False):
    if float:
        dtypes = [None, np.float16, np.float32, np.float64, np.float128]
    elif signed:
        dtypes = [np.int8, np.int16, np.int32, np.int64]
    else:
        dtypes = [np.uint8, np.uint16, np.uint32, np.uint64]

    dtype = None

    if size < len(dtypes):
        dtype = dtypes[size]

    if dtype is None:
        raise ValueError(f'Size {size} unsupported with signed={signed} and float={float}')

    return dtype


def nbytes2size(nbytes: Integral):
    if not isinstance(nbytes, Integral):
        raise ValueError(f'Number of bytes must be an integer (got {nbytes})')
    elif nbytes <= 0:
        raise ValueError(f'Number of bytes must be positive (got {nbytes})')

    nbytes = int(nbytes)

    if bin(nbytes).count('1') != 1:
        raise ValueError(f'Number of bytes must be a power of two (got {nbytes})')

    size = nbytes.bit_length() - 1

    if size < 0:
        raise ValueError(f'size cannot be negative (got {size})')

    return size


def dtype2size(dtype: np.dtype):
    if isinstance(dtype, np.dtype):
        return nbytes2size(dtype.itemsize)
    else:
        raise ValueError(f'dtype must be of type np.dtype (got {type(dtype)})')


def addr_aligned(addr: Integral, align: Integral) -> bool:
    return ((addr >> align) << align) == addr


def random_int_value(name, value, min, max, align=None):
    # determine the length of the transaction

    if isinstance(value, range) or (value is None):
        if isinstance(value, range):
            a = value.start
            b = value.stop - 1
        else:
            a = min
            b = max

        value = random.randint(a, b)

        if align is not None:
            value >>= align
            value <<= align
    elif isinstance(value, (list, tuple, np.ndarray)):
        value = random.choice(value)

        if isinstance(value, (range, list, tuple)):
            # if we happen to pick a range object from the list/tuple, then run this
            # function on the range object.  this allows users to specify a collection
            # of values and ranges to efficiently represent a discontinuous space
            # of options.  it is also possible to have lists of lists of ranges, to
            # adjust the probabilities of drawing from each range
            return random_int_value(name=name, value=value, min=min, max=max, align=align)

    # validate result

    check_int_in_range(name, value, min=min, max=max)

    value = int(value)

    if align is not None:
        if not addr_aligned(addr=value, align=align):
            raise ValueError(f'misaligned {name}: 0x{value:x}')

    # return result

    return value


def check_int_in_range(name, value, min=None, max=None):
    if not np.issubdtype(type(value), np.integer):
        raise ValueError(f'{name} is not an integer')

    if (min is not None) and (value < min):
        raise ValueError(f'{name} is less than {min}')

    if (max is not None) and (value > max):
        raise ValueError(f'{name} is greater than {max}')


def random_umi_packet(
    opcode=None,
    len=None,
    size=None,
    dstaddr=None,
    srcaddr=None,
    data=None,
    qos=0,
    prot=0,
    ex=0,
    atype=0,
    eom=1,
    eof=1,
    max_bytes=32
):
    """
    Generates a Random UMI packet. All parameters are optional. Parameters that
    are not explicitly specified will be assigned randomly.

    For more information on the meanings of each parameter, reference
    `the UMI specification <https://github.com/zeroasiccorp/umi/blob/main/README.md>`_

    Parameters
    ----------
    opcode: int, optional
        Command opcode

    len: int, optional
        Word transfers per message. (`len`-1 words will be transferred
        per message)

    size: int, optional
        Word size ((2^size)-1 bits per word)

    dstaddr: int, optional
        64-bit destination address used in the UMI packet

    srcaddr: int, optional
        64-bit source address used in the UMI packet

    data: numpy integer array, optional
        Values used in the Data field for the UMI packet

    qos: int, optional
        4-bit Quality of Service field used in the UMI command

    prot: int, optional
        2-bit Protection mode field used in the UMI command

    ex: int, optional
        1-bit Exclusive access indicator in the UMI command

    atype: int, optional
        8-bit field specifying the type of atomic transaction used
        in the UMI command for an atomic operation

    eom: int, optional
        1-bit End of Message indicator in UMI command, used to track
        the transfer of the last word in a message

    eof: int, optional
        1-bit End of Frame bit in UMI command, used to indicate the
        last message in a sequence of related UMI transactions

    max_bytes: int, optional
        The maximum number of bytes included in each UMI packet

    Returns
    -------
    """

    # input validation

    check_int_in_range("max_bytes", max_bytes, min=0, max=32)

    # TODO: make these parameters flexible, or more centrally-defined

    MAX_SUMI_SIZE = 3
    AW = 64

    # determine the opcode

    if opcode is None:
        opcode = random.choice([
            UmiCmd.UMI_REQ_WRITE,
            UmiCmd.UMI_REQ_POSTED,
            UmiCmd.UMI_REQ_READ,
            UmiCmd.UMI_RESP_WRITE,
            UmiCmd.UMI_RESP_READ,
            UmiCmd.UMI_REQ_ATOMIC
        ])
    elif isinstance(opcode, Iterable):
        opcode = random.choice(opcode)

    # determine the size of the transaction

    if (size is None) and (data is not None):
        size = dtype2size(data.dtype)

    size = random_int_value('size', size, 0, MAX_SUMI_SIZE)

    # determine the length of the transaction

    if (len is None) and (data is not None):
        len = data.size - 1

    len = random_int_value('len', len, 0, (max_bytes >> size) - 1)

    # generate other fields

    atype = random_int_value('atype', atype, 0x00, 0x08)
    qos = random_int_value('qos', qos, 0b0000, 0b1111)
    prot = random_int_value('prot', prot, 0b00, 0b11)
    eom = random_int_value('eom', eom, 0b0, 0b1)
    eof = random_int_value('eof', eof, 0b0, 0b1)
    ex = random_int_value('ex', ex, 0b0, 0b1)

    # construct the command field

    cmd = umi_pack(opcode, atype, size, len, eom, eof, qos, prot, ex)

    # generate destination address

    dstaddr = random_int_value('dstaddr', dstaddr, 0, (1 << AW) - 1, align=size)
    srcaddr = random_int_value('srcaddr', srcaddr, 0, (1 << AW) - 1, align=size)

    # generate data if needed

    if opcode in [
        UmiCmd.UMI_REQ_WRITE,
        UmiCmd.UMI_REQ_POSTED,
        UmiCmd.UMI_RESP_READ,
        UmiCmd.UMI_REQ_ATOMIC
    ]:
        if data is None:
            dtype = size2dtype(size)
            iinfo = np.iinfo(dtype)
            if opcode != UmiCmd.UMI_REQ_ATOMIC:
                nelem = len + 1
            else:
                nelem = 1
            data = np.random.randint(iinfo.min, iinfo.max - 1,
                size=nelem, dtype=dtype)

    # return the packet

    return PyUmiPacket(cmd=cmd, dstaddr=dstaddr, srcaddr=srcaddr, data=data)
