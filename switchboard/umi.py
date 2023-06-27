# Python interface for UMI reads, writes, and atomic operations
# Copyright (C) 2023 Zero ASIC

import numpy as np
from _switchboard import PyUmi, OldPyUmi, UmiCmd, OldUmiCmd

# note: it was convenient to implement some of this in Python, rather
# than have everything in C++, because it was easier to provide
# flexibility with numpy types


class UmiTxRx:
    def __init__(self, tx_uri="", rx_uri="", old=False):
        self.old = old

        if old:
            self.umi = OldPyUmi(tx_uri, rx_uri)
        else:
            self.umi = PyUmi(tx_uri, rx_uri)

    def init_queues(self, tx_uri="", rx_uri=""):
        self.umi.init(tx_uri, rx_uri)

    def send(self, p, blocking=True):
        """
        Sends (or tries to send if burst=False) a UMI transaction (PyUmiPacket object).
        The "data" field of the packet can contain more data than fits in a single
        UMI packet, in which case the beginning of the data will be sent in a header
        packet, and the rest will be sent as burst packets.
        """

        return self.umi.send(p, blocking)

    def recv(self, blocking=True):
        """
        Wait for and return a UMI packet (PyUmiPacket object) if blocking=True,
        otherwise return a UMI packet if one can be read immediately, and
        None otherwise.
        """

        return self.umi.recv(blocking)

    def write(self, addr, data, max_bytes=None, progressbar=False):
        """
        Writes the provided data to the given 64-bit address.  Data can be either
        a numpy integer type (e.g., np.uint32) or an numpy array of np.uint8's.

        The "max_bytes" argument (optional) indicates the maximum number of bytes
        that can be used for any individual UMI transaction, in bytes.

        The "data" input may contain more than "max_bytes", in which case
        the write will automatically be split into multiple transactions.

        Currently, the data payload size used by switchboard is 32 bytes,
        which is reflected in the default value of "max_bytes".
        """

        # set defaults

        if max_bytes is None:
            if self.old:
                max_bytes = (1 << 15)
            else:
                max_bytes = 32

        # format the data to be written

        if isinstance(data, np.ndarray):
            write_data = data
        elif isinstance(data, np.integer):
            write_data = np.array(data, ndmin=1, copy=False)
        else:
            raise TypeError(f"Unknown data type: {type(data)}")

        if self.old:
            write_data = write_data.view(np.uint8)

        # perform write

        self.umi.write(addr, write_data, max_bytes, progressbar)

    def write_readback(self, addr, value, mask=None, srcaddr=0, dtype=None):
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

    def read(self, addr, num_or_dtype, dtype=np.uint8, srcaddr=0, max_bytes=None):
        """
        Reads from the provided 64-bit address.  The "num_or_dtype" argument can be
        either a plain integer, specifying the number of bytes to be read, or
        a numpy integer datatype (e.g., np.uint32).

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
            if self.old:
                max_bytes = (1 << 15)
            else:
                max_bytes = 32

        if isinstance(num_or_dtype, (type, np.dtype)):
            len = 1
            size = np.dtype(num_or_dtype).itemsize
            return self.umi.read(addr, len, size, srcaddr, max_bytes).view(num_or_dtype)[0]
        else:
            len = num_or_dtype
            size = np.dtype(dtype).itemsize
            return self.umi.read(addr, len, size, srcaddr, max_bytes)

    def atomic(self, addr, data, opcode, srcaddr=0):
        """
        Applies an atomic operation to the provided 64-bit address.  "data" must
        be a numpy integer type (e.g., np.uint64), so that the size of the atomic
        operation can be determined.

        opcode should be drawn from switchboard.UmiCmd (e.g., UmiCmd.UMI_ATOMIC_AND),
        and indicates the type of atomic operation to be performed.

        The value returned by this function is the original value at addr,
        immediately before the atomic operation is applied.  The numpy dtype of the
        returned value will be the same as for "data".

        srcaddr is the UMI source address used for the atomic transaction.  This
        is sometimes needed to make sure the response get routed to the right place.
        """

        # resolve the opcode to an enum if needed
        if isinstance(opcode, str):
            # figure out what set of opcodes to use
            if self.old:
                opcode_enum = OldUmiCmd
            else:
                opcode_enum = UmiCmd

            # make sure that the string provided is in that opcode
            if opcode not in opcode_enum:
                raise ValueError(f'The provided opcode "{opcode}" does not appear to be valid.')

            # perform the conversion from string to enum
            opcode = opcode_enum[opcode]

        # format the data for sending
        if isinstance(data, np.integer):
            # copy=False should be safe here, because the data will be
            # copied over to the queue; the original data will never
            # be read again or modified from the C++ side
            atomic_data = np.array(data, ndmin=1, copy=False).view(np.uint8)
            return self.umi.atomic(addr, atomic_data, opcode, srcaddr).view(data.dtype)[0]
        else:
            raise TypeError("The data provided to atomic should be of a numpy integer type"
                " so that the transaction size can be determined")
