# xyce example

This example shows how to run a mixed-signal simulation of a Verilog module that instantiates a SPICE subcircuit.  The Verilog part can be simulated with Verilator or Icarus Verilog, while the SPICE part is simulated with Xyce.  

You can run the example with `make`, producing a `*.vcd` file where digital and analog waveforms may be inspected.  `make icarus` runs the simulation using Icarus Verilog as the digital simulator.  In either case, Xyce needs to be installed, including `XyceCInterface`.  If you don't have such a setup readily available, you can run this example using the `sbtest` Docker image, which includes Xyce, Verilator, and Icarus Verilog:

```shell
$ docker run --rm -it ghcr.io/zeroasiccorp/sbtest:latest bash
$ git clone https://github.com/zeroasiccorp/switchboard
$ cd switchboard
$ pip install -e .
$ cd examples/xyce
$ make
```

The core of the example code is the `input_analog()` call in [test.py](test.py):

```python
vdd = 1.0

params = dict(
    vol=0,
    voh=vdd,
    vil=0.2 * vdd,
    vih=0.8 * vdd
)

dut.input_analog(
    'mycircuit.cir',
    pins=[
        dict(name='a', type='input', **params),
        dict(name='b[1:0]', type='input', **params),
        dict(name='y', type='output', **params),
        dict(name='z[1:0]', type='output', **params),
        dict(name='vss', type='constant', value=0)
    ]
)
```

This code indicates that we want to instantiate a SPICE subcircuit defined in `mycircuit.cir` in our Verilog testbench.  The subcircuit name is inferred from the filename stem if not provided (`mycircuit` in this case).  The subcircuit name can also be provided explicitly via the `name` argument.  The `pins` argument describes how digital signals in the Verilog testbench interace with real-valued analog signals in the SPICE simulation.  For SPICE outputs, `vil` is the threshold below which a logical `0` will be driven to the Verilog simulation, and `vih` is the threshold above which a logical `1` will be driven.  For SPICE inputs, `vol` is the voltage that will be driven to the SPICE simulation when the corresponding Verilog signal is a logical `0`, and `voh` is the voltage driven for a logical `1`.  Other parameters include `tr`, `tf`, and `initial`, described in more detail in Switchboard documentation.

In the top-level Verilog file, [testbench.sv](testbench.sv), the SPICE subcircuit `mycircuit` is instantiated as an ordinary Verilog module:

```verilog
mycircuit mycircuit_i (
    .a(a),
    .b(b),
    .y(y),
    .z(z),
    .SB_CLK(clk)
);
```

Note the extra input called `SB_CLK`.  This is the oversampling clock; SPICE subcircuit outputs are driven to the Verilog simulation on positive edges of this clock.  If you want to reduce delay between the SPICE simulation and Verilog simulation, increase the frequency of `SB_CLK`.  However, this will reduce simulation speed.  In the future, we will explore techniques for eliminating this tradeoff.
