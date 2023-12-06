# fpga_loopback example

This example shows how to interact with a simulation of switchboard's FPGA infrastructure from Python.  The Python code is very similar to that of the [python](../python) example, except for the `build_testbench()` function, which builds a SystemC simulation.  The details of this simulation are in [testbench.cc](testbench.cc); in essence, SystemC AXI drivers are wired up to the AXI interface provided by `sb_fpga_queues`.  As in the [python](../python) example, `to_rtl.q` and `from_rtl.q` queues are created, and the [test.py](test.py) script interacts with these queues without having to know whether the other side is connected to DPI drivers in an RTL simulation, SystemC-based drivers, etc.

You won't typically need to run this kind of simulation, but it can be helpful when debugging changes to the FPGA infrastructure itself, since it is usually faster and more convenient to run a simulation vs. building a bitstream.

To run the example, type `make`.  You'll see a Verilator build, followed by output like this:

```text
*** TX packet ***
dest: 123456789
last: 1
data: [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31]

...

Addressing configuration for axi_crossbar_addr instance Top.dut.testbench.queues.crossbar.axi_crossbar_wr_inst.s_ifaces[0].addr_inst
 0 ( 0): 0000000000000000 / 64 -- 0000000000000000-ffffffffffffffff
Addressing configuration for axi_crossbar_addr instance Top.dut.testbench.queues.crossbar.axi_crossbar_wr_inst.s_ifaces[1].addr_inst
 0 ( 0): 0000000000000000 / 64 -- 0000000000000000-ffffffffffffffff
Addressing configuration for axi_crossbar_addr instance Top.dut.testbench.queues.crossbar.axi_crossbar_rd_inst.s_ifaces[0].addr_inst
 0 ( 0): 0000000000000000 / 64 -- 0000000000000000-ffffffffffffffff
Addressing configuration for axi_crossbar_addr instance Top.dut.testbench.queues.crossbar.axi_crossbar_rd_inst.s_ifaces[1].addr_inst
 0 ( 0): 0000000000000000 / 64 -- 0000000000000000-ffffffffffffffff

...

*** RX packet ***
dest: 123456789
last: 1
data: [ 1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
 25 26 27 28 29 30 31 32]

PASS!

Info: /OSCI/SystemC: Simulation stopped by user.
```
