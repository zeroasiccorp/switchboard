# Switchboard FPGA queues

This directory contains FPGA-synthesizable RTL that interacts with Switchboard
shared memory queues residing on a host CPU. This interaction occurs via direct
memory access controlled by AXI.

A simulation setup for testing this RTL can be found in `examples/fpga-loopback/`.

## Top-level interface

The main public interface of this RTL is meant to be either `sb_fpga_queues` (if you wish to work
directly with Switchboard packets), or `umi_fpga_queues` if you wish to work with UMI.

These two modules have analogous interfaces. They instantiate a parameterizable number of queues,
defined by `NUM_RX_QUEUES` and `NUM_TX_QUEUES`. They expose a single AXI manager interface that is
expected to provide direct memory access to a host device. These modules handle arbitrating access
to this port between all the queues instantiated.

**Important:** These modules currently have the limitation that `NUM_RX_QUEUES` and
`NUM_TX_QUEUES` must be equal, otherwise they may behave unexpectedly or fail to synthesize.

`umi_fpga_queues` is parameterized by the UMI data width (`DW`), address width (`AW`), and command
width (`CW`). The UMI ports on this module are wide 1-D bitvectors that concatenate the UMI signals
of each instantiated queue. For example, if an instance of `umi_fpga_queues` is defined with
`NUM_RX_QUEUES=2` and `AW=64`, `rx_dstaddr` will be of width 128, where `rx_dstaddr[63:0]` is wired
to the `dstaddr` signal of the first RX queue, and `rx_dstaddr[127:64]` is wired to the `dstaddr`
signal of the second RX queue.

`sb_fpga_queues` is parameterized by the Switchboard data width (`DW`), and its Switchboard
signals follow the same indexing scheme as `umi_fpga_queues`.

## Memory Map

This logic can be configured, controlled, and monitored by a set of registers
accessed by a subordinate AXI-Lite interface.

### Global

| **Address** | **Description** |
|-------------|-----------------|
| `0x00`       | Version/ID. Split into bitfields for ID [31:16], major version [15:9], and minor version [8:0]. (Read-only) |
| `0x04`       | Capability. Currently returns all zeros. (Read-only) |

### Per-queue

Each queue has its own 256-byte address space for per-queue configuration,
starting at `0x100` for the first queue, `0x200` for the second, etc.

| **Address offset** | **Description** |
|--------------------|-----------------|
| `0x00`             | Enable. Set to 1 to enable the queue. |
| `0x04`             | Reset. Set to 1 to soft-reset the queue. |
| `0x08`             | Status. Returns 1 if queue is in IDLE state, otherwise 0. (Read-only) |
| `0x0c`             | Base address low. Lower 32-bits of physical address of shared memory queue. |
| `0x10`             | Base address high. Upper 32-bits of physical address of shared memory queue. |
| `0x14`             | Capacity. Capacity of shared memory queue. |

The queue indexing scheme alternates between RX and TX queues.  For example, if an instance of
`umi_fpga_queues` or `sb_fpga_queues` is created with `NUM_RX_QUEUES=2` and `NUM_TX_QUEUES=2`, then
they are indexed as follows:

| Index/base addr. | Description |
| ----------- | ---------- |
| 0 / `0x100` | RX queue 0 |
| 1 / `0x200` | TX queue 0 |
| 2 / `0x300` | RX queue 1 |
| 3 / `0x400` | TX queue 1 |

### User registers

The configuration register module provides functionality for configuring up to 13 32-bit "user
registers" that can be used for application-specific purposes. The values of these registers are
exposed by the `cfg_user` output of the `sb_fpga_queues`/`umi_fpga_queues` modules. The number of
configuration registers is parameterized by the `NUM_USER_REGS` parameter of these modules.

| **Address** | **Description**  |
|-------------|------------------|
| `0x08`      | User register 0  |
| `0x40`      | User register 1  |
| `0x50`      | User register 2  |
| ...         | ...              |
| `0xf0`      | User register 12 |

Note that the register map is a bit inconsistent and sparse (for backwards compatibility). User
register 0 is located at address `0x8`, while the remaining user registers start at `0x40` and are
offset by `0x10` bytes.

## Software

`switchboard/cpp/switchboard_pcie.hpp` defines two classes `SBTX_pcie` and `SBRX_pcie` that inherit
from `SBTX` and `SBRX` and handle configuration of the FPGA queues. These classes are written in an
implementation-specific way that assumes the queue configuration registers are accessible via a PCIe
BAR.

To support other systems, a user can define new classes that inherit from these and overwrite the
`dev_read32`, `dev_write32`, and `dev_write32_strong` methods. See
`switchboard/cpp/switchboard_tlm.hpp` for an example of this.

The constructor of these classes takes in a queue index, which corresponds to the indexing scheme
used by the [per-queue address map](#per-queue). Note, however, that the naming scheme is reversed -
since these classes are named from a host perspective, and the FPGA queues are named from the
FPGA/device perspective, `SBTX_pcie` queues need to be constructed with RX queue indices, and
vice-versa for `SBRX_pcie` queues. For example, to communicate with a device that has 2 queue pairs,
queue objects could be instantiated in host software as follows:

```cpp
SBTX_pcie tx0(0);
SBTX_pcie tx1(2);
SBRX_pcie rx0(1);
SBRX_pcie rx1(3);
```

Keep in mind that these objects deinitialize their corresponding FPGA queue when destructed. This
means that the objects need to remain in-scope while a host is interacting with the FPGA queues, and
it's important to ensure that the program exits cleanly and calls the destructors in order to safely
de-init the logic on the FPGA side. Otherwise, the FPGA may attempt to access host memory after it
gets re-allocated for another purpose, leading to possible system instability on the host and/or
FPGA side.

## Dependencies

- Several modules require https://github.com/alexforencich/verilog-axi, see the submodule in `examples/deps/` for a supported version.
- If the `DEBUG` macro is defined, you must configure a Xilinx ILA module `ila_0` with the following probe widths:
    - `probe0 [0:0]`
    - `probe1 [63:0]`
    - `probe2 [0:0]`
    - `probe3 [0:0]`
    - `probe4 [63:0]`
    - `probe5 [0:0]`
