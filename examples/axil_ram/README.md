# axil example

NOTE: This example is similar to the one in axil. However, while axil auto generates the testbenches using the `interfaces` feature of `SbDut`, this example demonstrates a manual testbench using the switchboard axil module.

This example shows how to interact with AXI-Lite subordinates using switchboard.  A Python script writes random data to an AXI-Lite memory implementation ([this one](https://github.com/alexforencich/verilog-axi/blob/master/rtl/axil_ram.v)).  Data is then read back from the memory in a random order and compared against a local model.

To run the example, type `make`.  You'll see a Verilator build, followed by output like this:

```text
Read addr=0 data=[0xef 0x0 0x0 0x0]
Read addr=0 data=[0xef 0xbe 0x0 0x0]
Read addr=0 data=[0xef 0xbe 0xad 0xde]
Read addr=200 data=[0xa0 0xa0 0xa0 0xa0]
Read addr=0 data=[0xef 0xbe 0xad 0xde]
```

`make icarus` runs the example using Icarus Verilog as the digital simulator.

In the Verilog implementation, [testbench.sv](testbench.sv) instantiates a switchboard module that acts as an AXI-Lite manager.

The init method defines that the switchboard queues to be used start with the prefix `sb_axil_m`: `sb_axil_m-aw.q`, `sb_axil_m-w.q`, `sb_axil_m-b.q`, `sb_axil_m-ar.q`, `sb_axil_m-r.q`.

In the Python script [test.py](test.py), a corresponding `AxiLiteTxRx` object is created, using the same shorthand for connecting to all 5 queues.

```python
axil = AxiLiteTxRx('sb_axil_m', data_width=..., addr_width=...)
```

As with `UmiTxRx`, this object may be used to issue read and write transactions involving numpy scalars and arrays.  Under the hood, each transaction may be converted to multiple cycles of AXI transactions, with the write strobe automatically calculated in each cycle.

```python
axil.write(0, np.uint8(0xef))
read_data = axil.read(0, 4)  # read_data will contain 0xef
```

The `dtype` can be something other than a byte (even if the data type is wider than `data_width`)

```python
axil.write(0, np.uint32(0xdeadbeef))
read_data = axil.read(0, 4)  # read_data will contain 0xdeadbeef
```
