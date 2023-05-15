# Switchboard FPGA queues

This directory contains FPGA-synthesizable RTL that interacts with Switchboard
shared memory queues residing on a host CPU. This interaction occurs via direct
memory access controlled by AXI.

A demo using this RTL on AWS F1 can be found here:
https://github.com/zeroasiccorp/aws-fpga. In this example, host memory access is
performed via PCIe bus mastering, and the config registers are mapped to a PCIe
BAR. A corresponding software example can be found in `examples/pcie-ping/`.

A simulation setup for testing this RTL can be found in `examples/fpga-loopback/`.

## Memory Map

This logic can be configured, controlled, and monitored by a set of registers
accessed over an AXI-Lite interface.

### Global

| **Address** | **Description** |
|-------------|-----------------|
| `0x00`       | Version/ID. Split into bitfields for ID [31:16], major version [15:9], and minor version [8:0]. (Read-only) |
| `0x04`       | Capability. Currently returns all zeros. (Read-only) |
| `0x08`       | Clock divider. Used to program a clock divider that may be implemented at a design top-level. The effective clock speed becomes the value set in this register plus 1 (e.g. a value of 0 means no change in speed, a value of 2 means run at one third the speed). |

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

## Dependencies

- Several modules require https://github.com/alexforencich/verilog-axi, see the submodule in `examples/deps/` for a supported version.
- If the `DEBUG` macro is defined, you must configure a Xilinx ILA module `ila_0` with the following probe widths:
    - `probe0 [0:0]`
    - `probe1 [63:0]`
    - `probe2 [0:0]`
    - `probe3 [0:0]`
    - `probe4 [63:0]`
    - `probe5 [0:0]`
