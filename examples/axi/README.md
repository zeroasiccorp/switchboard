# axi example

This example shows how to interact with AXI subordinates using switchboard.  A Python script writes random data to an AXI memory implementation ([this one](https://github.com/alexforencich/verilog-axi/blob/master/rtl/axi_ram.v)).  Data is then read back from the memory in a random order and compared against a local model.

To run the example, type `make`.  You'll see a Verilator build, followed by output like this:

```text
Wrote addr=0xa9 data=[204 151 236 115 123 156 212  84 147]
Wrote addr=0xdc data=[181 183  45 240]
Wrote addr=0xc6 data=[ 84 235  19  16 103]
Wrote addr=0xa6 data=[177 195  66  57 208]
Read addr=0x1f data=[140 199  71]
Wrote addr=0x61 data=[233 182 131 230 213 188  23 178  44  99]
PASS!
```

`make icarus` runs the example using Icarus Verilog as the digital simulator.

In the Verilog implementation, [testbench.sv](testbench.sv) instantiates a switchboard module that acts as an AXI manager.

```verilog
`include "switchboard.vh"

...

`SB_AXI_M(sb_axi_m_i, axi, DATA_WIDTH, ADDR_WIDTH, ID_WIDTH);
```

Based on the macro arguments, the module instance is called `sb_axi_m_i` and it connects to AXI signals starting with the prefix `axi`.  The module is configured to connect to switchboard queues in an `initial` block:

```verilog
initial begin
    sb_axi_m_i.init("axi");
end
```

The argument, `axi`, is the prefix used when connecting to the queues that convey AXI traffic.  Since AXI has 5 channels, 5 queues will be connected as a result of this function call: `axi-aw.q`, `axi-w.q`, `axi-b.q`, `axi-ar.q`, `axi-r.q`.  If the argument of `init` were instead `myqueue`, then the queue names would all start with `myqueue` instead of `axi`.

In the Python script [test.py](test.py), a corresponding `AxiTxRx` object is created, using the same shorthand for connecting to all 5 queues.

```python
axi = AxiTxRx('axi', data_width=..., addr_width=..., id_width=...)
```

As with `UmiTxRx`, this object may be used to issue read and write transactions involving numpy scalars and arrays.  Under the hood, each transaction may be converted to multiple cycles of AXI transactions, with the write strobe automatically calculated in each cycle.

```python
axi.write(0x12, np.uint8(0x34))
value = axi.read(0x12, np.uint8)  # value will contain 0x34
```

The `dtype` can be something other than a byte (even if the data type is wider than `data_width`)

```python
axi.write(0x12, np.uint64(0xdeadbeefcafed00d))
value = axi.read(0x12, np.uint64)  # value will contain deadbeefcafed00d
```

It is also possible to read/write numpy arrays

```python
axi.write(0x12, np.array([0x1234, 0x5678], dtype=np.uint16))
value = axi.read(0x12, 2, np.uint16)  # value will contain [0x1234, 0x5678]
```
