# axil example

This example shows how to interact with AXI-Lite subordinates using switchboard.  A Python script writes random data to an AXI-Lite memory implementation ([this one](https://github.com/alexforencich/verilog-axi/blob/master/rtl/axil_ram.v)).  Data is then read back from the memory in a random order and compared against a local model.

To run the example, type `make`.  You'll see a Verilator build, followed by output like this:

```text
Wrote addr=0x6390 data=0x929e7155
Wrote addr=0xbb68 data=0xe39d766e
Wrote addr=0xfbf4 data=0x2f094521
Read addr=0xfbf4 data=0x2f094521
Read addr=0xbb68 data=0xe39d766e
Read addr=0x6390 data=0x929e7155
PASS!
```

`make icarus` runs the example using Icarus Verilog as the digital simulator.

Looking at the implementation, [testbench.sv](testbench.sv) instantiates a switchboard module called `sb_axil_m`, which acts as an AXI-Lite manager:

```verilog
sb_axil_m sb_axil_m_i (
    .clk(clk),
    .m_axil_awaddr(axil_awaddr),
    .m_axil_awprot(axil_awprot),
    ...
);
```

This module is configured in an `initial` block to connect to switchboard queues:

```verilog
initial begin
    sb_axil_m_i.init("axil");
end
```

The argument, `axil`, is the prefix used when connecting to the switchboard queues that convey AXI-Lite traffic.  Since AXI-Lite has 5 channels, 5 switchboard queues will be connected as a result of this function call: `axil-aw.q`, `axil-w.q`, `axil-b.q`, `axil-ar.q`, `axil-r.q`.  If the argument of `init` were instead `myqueue`, then the queue names would all start with `myqueue` instead of `axil`.

In the Python script [test.py](test.py), a corresponding `AxiLiteTxRx` object is created, using the same shorthand for connecting to all 5 queues.

```python
axil = AxiLiteTxRx('axil')
```

As with `UmiTxRx`, this object can be used to issue read and write transactions, e.g.

```python
axil.write(addr=0x12, data=0x34)
value = axil.read(addr=0x12)  # value will contain 0x34
```
