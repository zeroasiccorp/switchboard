# Python interface for UMI reads, writes, and atomic operations

# Copyright (c) 2023 Zero ASIC Corporation
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
        max_bytes: int = None, fresh: bool = False):
        """
        Args:
            tx_uri (str, optional): Name of the switchboard queue that
            write() and send() will send UMI packets to.  Defaults to
            None, meaning "unused".
            rx_uri (str, optional): Name of the switchboard queue that
            read() and recv() will receive UMI packets from.  Defaults
            to None, meaning "unused".
            srcaddr (int, optional): Default srcaddr to use for reads,
            ack'd writes, and atomics.  Defaults to 0.  Can also be
            provided as a dictionary with separate defaults for each
            type of transaction: srcaddr={'read': 0x1234, 'write':
            0x2345, 'atomic': 0x3456}.  When the defaults are provided
            with a dictionary, all keys are optional.  Transactions
            that are not specified in the dictionary will default
            to a srcaddr of 0.
            posted (bool, optional): If True, default to using posted
            (i.e., non-ack'd) writes.  This can be overridden on a
            transaction-by-transaction basis.  Defaults to False.
            max_bytes (int, optional): Default maximum number of bytes
            to use in each UMI transaction.  Can be overridden on a
            transaction-by-transaction basis.  Defaults to 32 bytes.
        """

        if tx_uri is None:
            tx_uri = ""

        if rx_uri is None:
            rx_uri = ""

        self.umi = PyUmi(tx_uri, rx_uri, fresh)

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

        Args:
            iwidth (int): Width of GPIO input (bits). Defaults to 32.
            owidth (int): Width of GPIO output (bits). Defaults to 32.
            init (int): Default value of GPIO output. Defaults to 0.
            dstaddr (int): Base address of the GPIO device. Defaults to 0.
            srcaddr (int): Source address to which responses should be routed. Defaults to 0.
            posted (bool): Whether writes should be sent as posted. Defaults to False.
            max_bytes (int): Maximum number of bytes in a single transaction to umi_gpio.
        Returns:
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
        Args:
            tx_uri (str, optional): Name of the switchboard queue that
            write() and send() will send UMI packets to.  Defaults to
            None, meaning "unused".
            rx_uri (str, optional): Name of the switchboard queue that
            read() and recv() will receive UMI packets from.  Defaults
            to None, meaning "unused".
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
        """

        return self.umi.send(p, blocking)

    def recv(self, blocking=True) -> PyUmiPacket:
        """
        Wait for and return a UMI packet if blocking=True, otherwise return a
        UMI packet if one can be read immediately, and None otherwise.  The return
        type (if not None) is a PyUmiPacket.
        """

        return self.umi.recv(blocking)

    def write(self, addr, data, srcaddr=None, max_bytes=None,
        posted=None, qos=0, prot=0, progressbar=False, check_alignment=True):
        """
        Writes the provided data to the given 64-bit address.  Data can be either
        a numpy integer type (e.g., np.uint32) or an numpy array of integer types
        (np.uint8, np.uin16, np.uint32, np.uint64, etc.).

        The "max_bytes" argument (optional) indicates the maximum number of bytes
        that can be used for any individual UMI transaction, in bytes.

        The "data" input may contain more than "max_bytes", in which case
        the write will automatically be split into multiple transactions.

        Currently, the data payload size used by switchboard is 32 bytes,
        which is reflected in the default value of "max_bytes".
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
            write_data = np.array(data, ndmin=1, copy=False)
        else:
            raise TypeError(f"Unknown data type: {type(data)}")

        if check_alignment:
            size = dtype2size(write_data.dtype)
            if not addr_aligned(addr=addr, align=size):
                raise ValueError(f'addr=0x{addr:x} misaligned for size={size}')

        # perform write
        self.umi.write(addr, write_data, srcaddr, max_bytes,
                       posted, qos, prot, progressbar)

    def write_readback(self, addr, value, mask=None, srcaddr=None, dtype=None,
        posted=True, write_srcaddr=None, check_alignment=True):
        """
        Writes the provided value to the given 64-bit address, and blocks
        until that value is read back from the provided address.

        The value can be a plain integer or a numpy integer type.  If it's a
        plain integer, then dtype must be specified, indicating a particular
        numpy integer type (e.g., np.uint16).  This is so that the size of the
        UMI transaction can be set appropriately.

        The "mask" argument (optional) allows the user to mask off some bits
        in the comparison of the data written vs. data read back.  For example,
        if a user only cares that bit "5" is written to "1", and does not care
        about the value of other bits read back, they could use mask=1<<5.

        srcaddr is the UMI source address used for the read transaction.  This
        is sometimes needed to make sure that reads get routed to the right place.

        By default, the write is performed as a posted write, however it is
        is possible to use an ack'd write by setting posted=False.  In that
        case, write_srcaddr specifies the srcaddr used for that transaction.
        If write_srcaddr is None, the default srcaddr for writes will be
        be used.
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
            check_alignment=check_alignment)
        rdval = self.read(addr, value.dtype, srcaddr=srcaddr, check_alignment=check_alignment)
        while ((rdval & mask) != (value & mask)):
            rdval = self.read(addr, value.dtype, srcaddr=srcaddr, check_alignment=check_alignment)

    def read(self, addr, num_or_dtype, dtype=np.uint8, srcaddr=None,
        max_bytes=None, qos=0, prot=0, check_alignment=True):
        """
        Reads from the provided 64-bit address.  The "num_or_dtype" argument can be
        either a plain integer, specifying the number of bytes to be read, or a numpy
        integer datatype (np.uint8, np.uint16, np.uint32, np.uint64, etc.).

        If num_or_dtype is a plain integer, the value returned by this function
        will be a numpy array of type "dtype".  On the other hand, if num_or_dtype
        is a numpy datatype, the value returned will be a scalar of that datatype.

        srcaddr is the UMI source address used for the read transaction.  This
        is sometimes needed to make sure that reads get routed to the right place.

        The "max_bytes" argument (optional) indicates the maximum number of bytes
        that can be used for any individual UMI transaction.

        The number of bytes to be read may be larger than max_bytes, in which
        case the read will automatically be split into multiple transactions.

        Currently, the data payload size used by switchboard is 32 bytes,
        which is reflected in the default value of "max_bytes".
        """

        # set defaults

        if max_bytes is None:
            max_bytes = self.default_max_bytes

        max_bytes = int(max_bytes)

        if srcaddr is None:
            srcaddr = self.def_read_srcaddr

        srcaddr = int(srcaddr)

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

        extra_args = []
        extra_args += [qos, prot]

        result = self.umi.read(addr, num, bytes_per_elem, srcaddr, max_bytes, *extra_args)

        if isinstance(num_or_dtype, (type, np.dtype)):
            return result.view(num_or_dtype)[0]
        else:
            return result

    def atomic(self, addr, data, opcode, srcaddr=None, qos=0, prot=0):
        """
        Applies an atomic operation to the provided 64-bit address.  "data" must
        be a numpy integer type (np.uint8, np.uint16, np.uint32, np.uint64), so that
        the size of the atomic operation can be determined.

        opcode may be a string or a value drawn from switchboard.UmiAtomic.  Supported
        string values are 'add', 'and', 'or', 'xor', 'max', 'min', 'minu', 'maxu',
        and 'swap' (case-insensitive).

        The value returned by this function is the original value at addr,
        immediately before the atomic operation is applied.  The numpy dtype of the
        returned value will be the same as for "data".

        srcaddr is the UMI source address used for the atomic transaction.  This
        is sometimes needed to make sure the response get routed to the right place.
        """

        # set defaults

        if srcaddr is None:
            srcaddr = self.def_atomic_srcaddr

        srcaddr = int(srcaddr)

        # resolve the opcode to an enum if needed
        if isinstance(opcode, str):
            opcode = getattr(UmiAtomic, f'UMI_REQ_ATOMIC{opcode.upper()}')

        extra_args = []
        extra_args += [qos, prot]

        # format the data for sending
        if isinstance(data, np.integer):
            # copy=False should be safe here, because the data will be
            # copied over to the queue; the original data will never
            # be read again or modified from the C++ side
            atomic_data = np.array(data, ndmin=1, copy=False).view(np.uint8)
            result = self.umi.atomic(addr, atomic_data, opcode, srcaddr, *extra_args)
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

    if value is None:
        value = random.randint(min, max)
        if align is not None:
            value >>= align
            value <<= align
    elif isinstance(value, Iterable):
        value = random.choice(value)

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
