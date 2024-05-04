# network example

This example demonstrates two new switchboard features: the ability to automatically generate Verilog wrappers wiring up DUT ports to switchboard modules, and the ability to dynamically construct networks of simulations that communication through switchboard connections.

The system in this example consists of an AXI-Lite memory connected to a UMI <-> AXI-Lite bridge from the UMI repository.  The UMI input and output of that bridge are each connected to a UMI FIFO.  The idea is that a Python script will send UMI transactions that are buffered by the FIFOs, converted to AXI-Lite by the bridge, and executed by the AXI-Lite memory.

<img width="473" alt="image" src="https://github.com/zeroasiccorp/switchboard/assets/19254098/ec9bc6b8-2e49-4b30-b9e4-4c6012e5924d" />

What is unusual here is that each of these four modules is run in a separate Verilator simulation.  Three simulator builds are run: one for the FIFO, one for the bridge, and one for the memory.  When the network simulation starts, two instances of the FIFO simulator are started, and one instance each of the other simulators are started.

Looking at the implementation in [test.py](test.py), the first step is to create an `SbNetwork` object.  Then, create `SbDut` objects for each unique module in the network (in this case, three).  For each of these objects, use the new `autowrap=True` feature and specify the interfaces on the module using the `interfaces` argument.  `interfaces` is a dictionary mapping the prefix of an interface to a dictionary of properties.  That dictionary should at a minimum contain keys for `type` (`axi`, `axil`, `umi`, `sb`) and direction (`input`/`output` for `umi` and `sb`, `manager`/`subordinate` for `axi` and `axil`).  Other properties include `dw`, `cw`, `aw`, `idw`.

Other arguments related to `autowrap` include:
* `parameters`: dictionary mapping the name of the module parameter to its value
* `clocks`: list of strings indicating inputs on the module that should be connected to the generated simulation clock
* `resets`: list of strings indicating inputs on the module that should be connected to the generated reset signal.  Optionally, entries in the list can be a dictionary that contains additional properties such as polarity.
* `tieoffs`: dictionary mapping the name of a module input to the value it should be wired to.  In the future, it will be possible to program tieoffs at runtime instead of having them fixed for a simulation build.  This is make it possible to build a module once and instantiate it multiple times with different tieoffs.

Once the `SbDut` objects are created, they are instantiated one or more times in the network the `SbNetwork.instantiate()`.  The `instantiate()` method returns an object with properties named after the interfaces.  This allows instances to be wired up the the `SbNetwork.connect()` method, e.g.

```python
net.connect(umi_fifo_i.umi_out, umi2axil_i.udev_req)
net.connect(umi_fifo_o.umi_in, umi2axil_i.udev_resp)
```

For interfaces that should be made available to the Python script, mark them external, e.g.

```python
net.external(umi_fifo_i.umi_in, txrx='umi')
net.external(umi_fifo_o.umi_out, txrx='umi')
```

The optional `txrx` argument is UMI-specific and means that the two interaces should be presented under a single `UmiTxRx` interface called `umi` (rather than two interfaces called `umi_in` and `umi_out`).

After calling `SbNetwork.build()` and `SbNetwork.simulate()`, the externally visible interfaces can be retrieved from the `SbNetwork.intfs` dictionary, just as for `SbDut`.
