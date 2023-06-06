# Copyright (C) 2023 Zero ASIC

# in the future, there may be some functions implemented directly in Python
# for now, though, all of the functionality is implemented in C++

from _switchboard import (PySbPacket, delete_queue, umi_opcode_to_str,  # noqa: F401
    PySbTx, PySbRx, UmiCmd, PySbTxPcie, PySbRxPcie, PyUmiPacket)

from .umi import UmiTxRx  # noqa: F401

try:
    from ._version import __version__
except ImportError:
    # This only exists in installations
    __version__ = None
