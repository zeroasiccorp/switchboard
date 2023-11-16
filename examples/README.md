# Switchboard examples

This directory contains a number of examples showing how to use switchboard as a Python or C++ library, as well as how to integrate it into RTL for simulation.

We suggest that you start with the [umiram tutorial](umiram).  This shows how to integrate switchboard modules into testbench RTL, how to compile a testbench with Verilator, and how to interact with the resulting RTL simulator from Python.  It's also a good introduction to the `read()`, `write()`, and `atomic()` operations in [UMI](https://github.com/zeroasiccorp/umi).

Other examples of using switchboard to interact with UMI-based RTL modules include:
* [umi_endpoint](umi_endpoint): Module that converts UMI packets to signaling for an SRAM (write enable, read/write address, etc.).
* [umi_fifo](umi_fifo): Module that buffers UMI packets.
* [umi_fifo_flex](umi_fifo): Module that serves as an adapter between UMI buses with different data widths, by splitting UMI packets according to [rules in the UMI specification](https://github.com/zeroasiccorp/umi#411-splitting-rules).
* [umi_gpio](umi_gpio): Demonstrates a mechanism for bit-level interaction with RTL through slice accesses in Python.  This can be a convenient mechanism for controlling non-UMI signals.
* [umi_splitter](umi_gpio): Module that routes UMI packets to one of two destinations according to the address.

[umi_mem_cpp](umi_mem_cpp) is a bit different: it shows how to model a UMI memory using switchboard's C++ library, without RTL.  The test logic is still driven from Python.

If you're interested in using SW modeling for an interface other than UMI, check out the [minimal](minimal) example.  This demonstrates how to read and write data payloads from C++, and use these payloads to interact with a running RTL simulation.  It's also an example of how to switch between the Verilator and Icarus Verilog simulators (summary: set `tool='icarus'` or `tool='verilator'` when you instantiate `SbDut`).

The [python](python) example is similar to the [minimal](minimal) example, except that the interaction with RTL is driven with Python instead of from C++.  This is often a convenient way to get started with test development, later moving some of the implementation to C++ if needed for performance reasons.

We also provide a mechanism for bridging switchboard connections over TCP, which may be useful if you're running a simulation or FPGA-based emulator on one machine, but want to interact with it from another machine.  The [tcp example](tcp) shows how to set this up; it's mostly a matter of calling `start_tcp_bridge` on the server and client sides.
