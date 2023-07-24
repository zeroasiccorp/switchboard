# Python interface for UMI reads, writes, and atomic operations
# Copyright (C) 2023 Zero ASIC

import random
import numpy as np
from typing import Iterable, Union
from _switchboard import (PyUmi, PyUmiPacket, umi_pack, UmiCmd, UmiAtomic,
    OldPyUmi, OldUmiCmd, OldPyUmiPacket)

# note: it was convenient to implement some of this in Python, rather
# than have everything in C++, because it was easier to provide
# flexibility with numpy types


class UmiTxRx:
    def __init__(self, tx_uri: str = None, rx_uri: str = None, old: bool = False,
        srcaddr: int = 0, posted: bool = False, max_bytes: int = None):
        """
        Args:
            tx_uri (str, optional): Name of the switchboard queue that
            write() and send() will send UMI packets to.  Defaults to
            None, meaning "unused".
            rx_uri (str, optional): Name of the switchboard queue that
            read() and recv() will receive UMI packets from.  Defaults
            to None, meaning "unused".
            old (bool, optional): If True, use the old UMI protocol.
            Defaults to False.  This option will eventually be removed.
            srcaddr (int, optional): Default srcaddr to use for reads,
            ack'd writes, and atomics.  Defaults to 0.
            posted (bool, optional): If True, default to using posted
            (i.e., non-ack'd) writes.  This can be overridden on a
            transaction-by-transaction basis.  Defaults to False.
            max_bytes (int, optional): Default maximum number of bytes
            to use in each UMI transaction.  Can be overridden on a
            transaction-by-transaction basis.  Defaults to 32 bytes
            when old=False and 32kB when old=True.
        """

        if tx_uri is None:
            tx_uri = ""

        if rx_uri is None:
            rx_uri = ""

        self.old = old

        if old:
            self.umi = OldPyUmi(tx_uri, rx_uri)
        else:
            self.umi = PyUmi(tx_uri, rx_uri)

        if srcaddr is not None:
            self.default_srcaddr = int(srcaddr)
        else:
            raise ValueError('Default value of "srcaddr" cannot be None.')

        if posted is not None:
            self.default_posted = bool(posted)
        else:
            raise ValueError('Default value of "posted" cannot be None.')

        if max_bytes is None:
            if old:
                max_bytes = (1 << 15)
            else:
                max_bytes = 32

        self.default_max_bytes = max_bytes

    def init_queues(self, tx_uri=None, rx_uri=None):
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

        self.umi.init(tx_uri, rx_uri)

    def send(self, p, blocking=True) -> bool:
        """
        Sends (or tries to send if burst=False) a UMI transaction (PyUmiPacket if
        old=False, OldPyUmiPacket if old=True).  Returns True if the packet was
        sent successfully, else False.
        """

        return self.umi.send(p, blocking)

    def recv(self, blocking=True) -> Union[PyUmiPacket, OldPyUmiPacket]:
        """
        Wait for and return a UMI packet if blocking=True, otherwise return a
        UMI packet if one can be read immediately, and None otherwise.  The return
        type (if not None) is a PyUmiPacket if old=False and OldPyUmiPacket if old=True
        """

        return self.umi.recv(blocking)

    def write(self, addr, data, srcaddr=None, max_bytes=None,
        posted=None, qos=0, prot=0, progressbar=False):
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
            srcaddr = self.default_srcaddr

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

        if self.old:
            write_data = write_data.view(np.uint8)

        # perform write
        if self.old:
            self.umi.write(addr, write_data, max_bytes, progressbar)
        else:
            self.umi.write(addr, write_data, srcaddr, max_bytes,
                posted, qos, prot, progressbar)

    def write_readback(self, addr, value, mask=None, srcaddr=None, dtype=None):
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
        """

        # set defaults

        if srcaddr is None:
            srcaddr = self.default_srcaddr

        srcaddr = int(srcaddr)

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
        self.write(addr, value)
        rdval = self.read(addr, value.dtype, srcaddr=srcaddr)
        while ((rdval & mask) != (value & mask)):
            rdval = self.read(addr, value.dtype, srcaddr=srcaddr)

    def read(self, addr, num_or_dtype, dtype=np.uint8, srcaddr=None,
        max_bytes=None, qos=0, prot=0):
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
            srcaddr = self.default_srcaddr

        srcaddr = int(srcaddr)

        if isinstance(num_or_dtype, (type, np.dtype)):
            len = 1
            size = np.dtype(num_or_dtype).itemsize
        else:
            len = num_or_dtype
            size = np.dtype(dtype).itemsize

        extra_args = []
        if not self.old:
            extra_args += [qos, prot]

        result = self.umi.read(addr, len, size, srcaddr, max_bytes, *extra_args)

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
            srcaddr = self.default_srcaddr

        srcaddr = int(srcaddr)

        # resolve the opcode to an enum if needed
        if isinstance(opcode, str):
            if self.old:
                opcode = getattr(OldUmiCmd, f'OLD_UMI_ATOMIC_{opcode.upper()}')
            else:
                opcode = getattr(UmiAtomic, f'UMI_REQ_ATOMIC{opcode.upper()}')

        extra_args = []
        if not self.old:
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


def dtype2size(dtype: np.dtype):
    if isinstance(dtype, np.dtype):
        itemsize = int(dtype.itemsize)

        if itemsize.bit_count() != 1:
            raise ValueError(f'itemsize must be a power of two (got {itemsize})')

        size = int(dtype.itemsize).bit_length() - 1

        if size < 0:
            raise ValueError(f'size cannot be negative (got {size})')

        return size
    else:
        raise ValueError(f'dtype must be of type np.dtype (got {type(dtype)})')


def random_int_value(name, value, min, max):
    # determine the length of the transaction

    if value is None:
        value = random.randint(min, max)
    elif isinstance(value, Iterable):
        value = random.choice(value)

    # validate result

    if int(value) != value:
        raise ValueError(f'{name} is not an integer: {value}')

    value = int(value)

    if not ((min <= value) and (value <= max)):
        raise ValueError(f'unsupported {name}: {value}')

    # return result

    return value


def random_umi_packet(opcode=UmiCmd.UMI_REQ_WRITE, len=None, size=None,
    dstaddr=None, srcaddr=None, data=None, qos=0, prot=0, ex=0,
    atype=0, eom=1, eof=1):

    # TODO: make these parameters flexible, or more centrally-defined

    MAX_SUMI_BYTES = 32
    MAX_SUMI_SIZE = 3
    AW = 64

    # determine the opcode

    if opcode is None:
        opcode = random.choice([
            UmiCmd.UMI_REQ_WRITE,
            UmiCmd.UMI_REQ_POSTED,
            UmiCmd.UMI_REQ_READ,
            UmiCmd.UMI_RESP_WRITE,
            UmiCmd.UMI_RESP_READ
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

    len = random_int_value('len', len, 0, (MAX_SUMI_BYTES >> size) - 1)

    # generate other fields

    atype = random_int_value('atype', atype, 0x00, 0xff)
    qos = random_int_value('qos', qos, 0b0000, 0b1111)
    prot = random_int_value('prot', prot, 0b00, 0b11)
    eom = random_int_value('eom', eom, 0b0, 0b1)
    eof = random_int_value('eof', eof, 0b0, 0b1)
    ex = random_int_value('ex', ex, 0b0, 0b1)

    # construct the command field

    cmd = umi_pack(opcode, atype, size, len, eom, eof, qos, prot, ex)

    # generate destination address

    dstaddr = random_int_value('dstaddr', dstaddr, 0, (1 << AW) - 1)
    srcaddr = random_int_value('srcaddr', srcaddr, 0, (1 << AW) - 1)

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
