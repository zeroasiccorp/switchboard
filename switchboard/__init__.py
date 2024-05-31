# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

# in the future, there may be some functions implemented directly in Python
# for now, though, all of the functionality is implemented in C++

from _switchboard import (PySbPacket, delete_queue, umi_opcode_to_str,
    PySbTx, PySbRx, UmiCmd, PySbTxPcie, PySbRxPcie, PyUmiPacket, umi_pack,
    umi_opcode, umi_size, umi_len, umi_atype, umi_qos, umi_prot, umi_eom,
    umi_eof, umi_ex, UmiAtomic, delete_queues)

from .umi import UmiTxRx, random_umi_packet
from .util import binary_run, ProcessCollection
from .verilator import verilator_run
from .icarus import icarus_build_vpi, icarus_run
from .sbdut import SbDut
from .loopback import umi_loopback
from .bitvector import BitVector
from .uart_xactor import uart_xactor
from .sbtcp import start_tcp_bridge
from .axil import AxiLiteTxRx
from .axi import AxiTxRx
from .network import SbNetwork, TcpIntf
from .autowrap import flip_intf
from .switchboard import path as sb_path
