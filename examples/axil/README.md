# axil example

This example shows how to interact with AXI-Lite subordinates using switchboard.  A Python script writes random data to an AXI-Lite memory implementation ([this one](https://github.com/alexforencich/verilog-axi/blob/master/rtl/axil_ram.v)).  Data is then read back from the memory in a random order and compared against a local model.

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

In the Python script [test.py](test.py), an AXI-Lite interface is specified using the `interfaces` argument of `SbDut`.  The name of the interface is `s_axil`, corresponding to the AXI-Lite port prefix in the `axil_ram` implementation.  After simulation starts, the AXI-Lite interface object is retrieved from the `SbDut.intfs` dictionary.

```python
interfaces = {
    's_axil': dict(type='axil', dw=dw, aw=aw, direction='subordinate')
}

...

dut = SbDut('axill_ram', ..., interfaces=interfaces, ...)

...

axi = dut.intfs['s_axil']  # type: AxiLiteTxRx
```

As with `UmiTxRx`, this object may be used to issue read and write transactions involving numpy scalars and arrays.  Under the hood, each transaction may be converted to multiple cycles of AXI transactions, with the write strobe automatically calculated in each cycle.

```python
axil.write(0x12, np.uint8(0x34))
value = axil.read(0x12, np.uint8)  # value will contain 0x34
```

The `dtype` can be something other than a byte (even if the data type is wider than `data_width`)

```python
axil.write(0x12, np.uint64(0xdeadbeefcafed00d))
value = axil.read(0x12, np.uint64)  # value will contain deadbeefcafed00d
```

It is also possible to read/write numpy arrays

```python
axil.write(0x12, np.array([0x1234, 0x5678], dtype=np.uint16))
value = axil.read(0x12, 2, np.uint16)  # value will contain [0x1234, 0x5678]
```
