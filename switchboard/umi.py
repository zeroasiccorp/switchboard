# Python interface for UMI reads, writes, and atomic operations
# Copyright (C) 2023 Zero ASIC

import numpy as np
from _switchboard import PyUmi, UmiCmd

# note: it was convenient to implement some of this in Python, rather
# than have everything in C++, because it was easier to provide
# flexibility with numpy types

class UmiTxRx:
    def __init__(self, tx_uri="", rx_uri=""):
        self.umi = PyUmi(tx_uri, rx_uri)
    
    def init_queues(self, tx_uri="", rx_uri=""):
        self.umi.init(tx_uri, rx_uri)

    def recv(self, blocking=True):
        """
        Wait for and return a UMI packet (PyUmiPacket object) if blocking=True,
        otherwise return a UMI packet if one can be read immediately, and
        None otherwise.
        """

        return self.umi.recv(blocking)

    def write(self, addr, data):
        """
        Writes the provided data to the given 64-bit address.  Data can be either
        a numpy integer type (e.g., np.uint32) or an numpy array of np.uint8's.
        """

        if isinstance(data, np.ndarray):
            self.umi.write(addr, data.view(np.uint8))
        elif isinstance(data, np.integer):
            # copy=False should be safe here, because the data will be
            # copied over to the queue; the original data will never
            # be read again or modified from the C++ side
            write_data = np.array(data, ndmin=1, copy=False).view(np.uint8)
            self.umi.write(addr, write_data)
        else:
            raise Exception(f"Unknown data type: {type(data)}")

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
                raise Exception("Must provide value as a numpy integer type, or specify dtype.")

        # set the mask to all ones if it is None
        if mask is None:
            nbits = (np.dtype(value.dtype).itemsize*8)
            mask = (1<<nbits) - 1

        # convert mask to a numpy datatype if it is not already
        if not isinstance(mask, np.integer):
            if dtype is not None:
                mask = dtype(mask)
            else:
                raise Exception("Must provide mask as a numpy integer type, or specify dtype.")

        # write, then read repeatedly until the value written is observed
        self.write(addr, value)
        rdval = self.read(addr, value.dtype, srcaddr=srcaddr)
        while ((rdval & mask) != (value & mask)):
            rdval = self.read(addr, value.dtype, srcaddr=srcaddr)

    def read(self, addr, num_or_dtype, srcaddr=0):
        """
        Reads from the provided 64-bit address.  The "num_or_dtype" argument can be
        either a plain integer, specifying the number of bytes to be read, or
        a numpy integer datatype (e.g., np.uint32).

        If num_or_dtype is a plain integer, the value returned by this function
        will be a numpy array of np.uint8 (an array of bytes).  If not, this
        function will return a numpy integer value of the given dtype.

        srcaddr is the UMI source address used for the read transaction.  This
        is sometimes needed to make sure that reads get routed to the right place.
        """

        if isinstance(num_or_dtype, (type, np.dtype)):
            size = np.dtype(num_or_dtype).itemsize
            return self.umi.read(addr, size, srcaddr).view(num_or_dtype)[0]
        else:
            return self.umi.read(addr, num_or_dtype, srcaddr)

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
            if opcode not in UmiCmd:
                raise Exception(f'The provided opcode "{opcode}" does not appear to be valid.')
            opcode = UmiCmd[opcode]

        # format the data for sending
        if isinstance(data, np.integer):
            # copy=False should be safe here, because the data will be
            # copied over to the queue; the original data will never
            # be read again or modified from the C++ side
            atomic_data = np.array(data, ndmin=1, copy=False).view(np.uint8)
            return self.umi.atomic(addr, atomic_data, opcode, srcaddr).view(data.dtype)[0]
        else:
            raise Exception("The data provided to atomic should be of a numpy integer type"
                " so that the transaction size can be determined")
