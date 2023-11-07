# Switchboard FPGA queues

This directory contains FPGA-synthesizable RTL that interacts with Switchboard
shared memory queues residing on a host CPU. This interaction occurs via direct
memory access controlled by AXI.

A simulation setup for testing this RTL can be found in `examples/fpga-loopback/`.

## Memory Map

This logic can be configured, controlled, and monitored by a set of registers
accessed over an AXI-Lite interface.

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

### User registers

The configuration register module also provides functionality for configuring up to 13 32-bit "user
registers" that can be used for application-specific purposes. The values of these registers are
exposed to a top-level design by the `cfg_user` output of the `sb_fpga_queues`/`umi_fpga_queues`
modules.

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

## Dependencies

- Several modules require https://github.com/alexforencich/verilog-axi, see the submodule in `examples/deps/` for a supported version.
- If the `DEBUG` macro is defined, you must configure a Xilinx ILA module `ila_0` with the following probe widths:
    - `probe0 [0:0]`
    - `probe1 [63:0]`
    - `probe2 [0:0]`
    - `probe3 [0:0]`
    - `probe4 [63:0]`
    - `probe5 [0:0]`
