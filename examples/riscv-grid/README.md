# riscv-grid example

This example constructs an MxN grid of PicoRV32 CPUs, each modeled with a Verilator simulation.  The (0, 0) location in the grid does not contain a CPU; instead, it is occupied by a program called `client` that programs the CPUs over UMI.  `client` can also receive UMI writes and interpret them as either characters to print, or an instruction to exit the emulator.

## Installation

Some additional software is required to run this example; see platform-specific instructions below.

### Linux

```shell
sudo apt-get install verilator gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
```

### macOS

```shell
brew tap riscv/riscv
```

```shell
brew install verilator riscv-tools
```

## Running the example

Tasks are run on the emulated grid via a Makefile.  For example, to run a "hello world" program (`riscv/hello.c`), in this folder run:

```shell
make hello
```

This constructs a `1x2` grid, with `client` at (0, 0), and a PicoRV32 CPU at (0, 1).  `client` programs the CPU with a program that sends a message over UMI back to `client`, and then sends a command to exit the emulator.

Other options include:
* `make grid`: Has the CPU in the bottom-right corner of the grid send a message back to `client`.
* `make addloop`: Passes a counter from one CPU to the next, incrementing it each time.  Once the counter hits a target value, the CPU where the target was hit sends a message back to `client`.

`grid` and `addloop` are both run using the script `grid.py`, which can construct an array of specified size via its `--row` and `--col` arguments.  The `--binfile` argument allows the location of the binary file to be programmed to the CPUs to be specified.

### Detail: address space

Programs running on the PicoRV32 processor can send writes out to their UMI port, as well as reading/writing their own internal memory.  Since PicoRV32 is a 32-bit processor, this is accomplished by partitioning the 32-bit address space:
* Bit 31 indicates if a write is external (if `1`) or internal (if `0`)
* Bits 30-27 indicate the *row* destination of an external write.
* Bits 26-23 indicate the *column* destination of an external write.
* Bits 22-0 are the local address for a read/write.

Note that in this example, up to 16 rows and 16 columns are supported (i.e., less than the full amount that will be possible in the chiplet array).  We may want to update the example at some point to use a 64-bit processor to remove this limitation.

### Detail: initialization

`client` programs the CPUs by first placing them all in reset via UMI writes that control GPIOs in the CPU hardware.  It then programs the internal memory of all CPUs, while they are in reset.

In the current configuration, the top 128 bytes of CPU internal memory are reserved for runtime parameters.  `client` populates the top 4 words of this space with the row and column of each CPU in the grid (unique for each location), as well as the total number of rows and columns.  It then programs additional parameters specified by the user, which may be used to control the runtime behavior of RISC-V programs.  For example, in `addloop` the target value is provided as a runtime parameter in this manner.

Runtime parameter initialization can also be used to initialize memory for inter-CPU communication.  For example, the counter used in `addloop` is initialized to zero using the runtime parameter feature.  This is necessary because once the CPUs are released from reset, it is not safe for them to initialize an externally writable location, because it might be clobbering a value written by another CPU.  At the same time, it cannot reliably read the memory contents at that location, since they might contain garbage, having not been initialized or externally written.
