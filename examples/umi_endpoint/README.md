# umi_endpoint example

`umi_endpoint` is a module from the [UMI repository](https://github.com/zeroasiccorp/umi) that converts UMI requests into memory control signals (`addr`, `write`, `read`, `wrdata`, `rddata`).  This example shows how to use switchboard to interact with the `umi_endpoint` module.  It's  similar to the [umiram](../umiram) example; we suggest going through that tutorial first if you haven't already.

Assuming that you have installed the switchboard package in your current Python environment, you can run this example with `./test.py`.  This will first build a Verilator simulator, and then interact with the simulated RTL using switchboard.  You'll see output similar to:

```text
### MINIMAL EXAMPLE ###
Read: 0xdeadbeef
### WRITES ###
### READS ###
Read: 0xbaadf00d
Read: 0xb0bacafe
Read: 0xdeadbeef
Read: 0xbaadd00dcafeface
```

Just as in the `umiram` example, Python code interacts with the simulation using `read()` and `write()` methods.  However, the RTL implementation in [testbench.sv](testbench.sv) is different than in `umiram`, because the `umi_endpoint` does not implement a memory, but instead acts as a translator between UMI requests and control signals for an external memory.  That memory is implemented directly in `testbench.sv` using an unpacked array; it consists of 256 64-bit words.
