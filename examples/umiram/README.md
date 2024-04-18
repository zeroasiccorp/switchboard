# umiram tutorial

Switchboard provides a Python interface for reading from and writing to RTL designs using [UMI](https://github.com/zeroasiccorp/umi).  This tutorial shows how to create such a setup, using a simple UMI memory design as an example.  You'll learn how to instantiate switchboard Verilog modules that connect to the DUT, and how to interact with the DUT from Python.

## Installation

If you haven't already cloned this repo and installed the switchboard Python package, please do that first.  We recommend installing switchboard in a virtual env, conda env, etc. to keep things tidy.

```console
git clone https://github.com/zeroasiccorp/switchboard.git
```

```console
cd switchboard
```

```console
git submodule update --init
```

```console
pip install --upgrade pip
```

```console
pip install -e .
```

```console
pip install -r examples/requirements.txt
```

## Structure

The RTL structure of this example is a Verilog module, [testbench](testbench.sv), that instantiates UMI memory, [umiram](../common/verilog/umiram.sv).  Within `testbench`, the UMI `udev_req` and `udev_resp` ports of `umiram` are terminated using the `queue_to_umi_sim` and `umi_to_queue_sim` modules provided by switchboard, instantiated using the `QUEUE_TO_UMI_SIM` and `UMI_TO_QUEUE_SIM` macros provided by `switchboard.vh`.

A Verilator simulation is built using `testbench` as the top level.  When it runs, UMI packets flow into `udev_req` from a switchboard queue, `to_rtl.q`, and flow out from `udev_resp` into a switchboard queue, `from_rtl.q`.  These queues will show up on your computer as ordinary files, each representing a region of shared memory.

In the Python script [test.py](test.py), a UMI driver is instantiated that sends packets to `to_rtl.q` and receives them from `from_rtl.q`.  `write()` and `read()` methods provided by the driver allow [numpy](https://numpy.org) arrays and scalars to be written to and read from the DUT, with each operation mapping to one or more UMI operations with automatically calculated [SIZE](https://github.com/zeroasiccorp/umi#332-transaction-word-size-size20) and [LEN](https://github.com/zeroasiccorp/umi#333-transaction-length-len70) parameters.

<img width="473" alt="image" src="https://github.com/zeroasiccorp/switchboard/assets/19254098/a7b65f14-40a5-480e-a297-5f5acf983f3e">

These operations are automated by the Python script.  If you haven't already, `cd` into this folder, and then execute `test.py`.  You should see the following output, after the Verilator build completes:

```text
$ ./test.py
...
### WRITES ###
### READS ###
Read: 0xbaadf00d
Read: 0xb0bacafe
Read: 0xdeadbeef
Read: 0xbaadd00dcafeface
...
```

In the sections that follow, we'll go into the different components of this example, to give a sense of how they might be modified for your own use.

## testbench.sv

The main purpose of the top-level module, `testbench`, is to instantiate the DUT and connect its UMI ports to switchboard-provided "end caps": `queue_to_umi_sim` and `umi_to_queue_sim`.  `queue_to_umi_sim` receives UMI packets from outside of the Verilog simulation and drives them into the DUT, while `umi_to_queue_sim` drives UMI packets to the outside world that are provided by the DUT.

Macros provided from `switchboard.vh` make it possible to instantiate and wire up each end cap with a single line of Verilog code.  The first argument of the macro is the prefix of the signals being connected.  For example, if the prefix is `udev_req`, the signals connected are `udev_req_data`, `udev_req_valid`, etc.  The name of the module instantiated is derived from this argument by appending the `_sb_inst` suffix.

```verilog
`QUEUE_TO_UMI_SIM(udev_req, DW, CW, AW, "to_rtl.q");
`UMI_TO_QUEUE_SIM(udev_resp, DW, CW, AW, "from_rtl.q");
```

The next three arguments specify the data width, command width, and address width of the UMI interface, respectively.  

The last argument is the name of the switchboard queue used to convey the UMI packets.  There is nothing special about the queue names; all legal file names can be used, as long as they match up to the names used in the SW driver.  For example, since the DUT is expecting to receive UMI packets from `to_rtl.q`, the Python script should be configured to send packets to `to_rtl.q`.  The switchboard queues are ordinary files, and they may stick around after a simulation.  For that reason, you may want to give them a globbable name so you can do things like `rm *.q`, or add `*.q` to `.gitignore`.

### Ready/valid behavior

Optional macro arguments control ready/valid behavior.  For `QUEUE_TO_UMI_SIM`, the next argument after the queue name is `VALID_MODE_DEFAULT`:

```verilog
`QUEUE_TO_UMI_SIM(prefix, DW, CW, AW, queue, vldmode);
```

* `vldmode`
    * `0` means to always set `valid` to `0` after completing a transaction.  This means that if there is a steady stream of data being driven out and `ready` is kept asserted, `valid` will alternate between `0` and `1`.
    * `1` means to try to keep `valid` asserted as much as possible, so if there is a constant stream of data being driven out and `ready` is kept asserted, `valid` will remain asserted.
    * `2` means to flip a coin before deciding to drive out the next packet.  This causes the `valid` line to have a random pattern if there is a constant stream of data to be driven and `ready` is kept asserted.

For `UMI_TO_QUEUE_SIM`, the next argument after the queue name is `READY_MODE_DEFAULT`:

```verilog
`UMI_TO_QUEUE_SIM(prefix, DW, CW, AW, queue, rdymode);
```

* `rdymode`
    * `0` means to hold off on asserting `ready` until `valid` has been asserted.
    * `1` means to assert `ready` as much as possible, so if `valid` is held high, `ready` will remain asserted as long as more packets can be pushed into the switchboard queue (i.e., as long as the SW driver isn't backpressuring)
    * `2` means to flip a coin on each cycle to determine if `ready` will be asserted in that cycle (provided that there is room in the switchboard queue)

Both `vldmode` and `rdymode` macro arguments are defaults that can be changed at runtime, using the `set_valid_mode` and `set_ready_mode` functions provided by `queue_to_umi_sim` and `umi_to_queue_sim` modules, respectively.  This means that the simulator doesn't have to be rebuilt to vary ready/valid behavior. 

### Clock generation

You may have noticed this block of code near the top of [testbench.sv](testbench.sv)

```verilog
`include "switchboard.vh"

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    `ifndef VERILATOR
        `SB_CREATE_CLOCK(clk)
    `endif
```

This is generally how switchboard testbenches should start, since it allows the same RTL to be used for Verilator and Icarus Verilog simulation.  The issue is that the clock signal is generated outside of the testbench in Verilator, but inside the testbench in Icarus Verilog.  The `SB_CREATE_CLOCK` macro takes care of creating the clock when Icarus Verilog is being used, and provides additional features, such as being able to change the simulation frequency at runtime.

### Waveform probing

Another macro provided with `switchboard.vh` 

```verilog
`SB_SETUP_PROBES
```

## test.py

This is a Python script that builds the Verilator simulator, launches it, and interacts with the running RTL simulation of `umiram`.

### Simulator build

The logic for building the Verilator simulator is found in `build_testbench()`.  As a convenience, `switchboard` provides a class called `SbDut` that inherits from `siliconcompiler.Chip` and abstracts away switchboard-specific setup required for using the `queue_to_umi_sim` and `umi_to_queue_sim` modules in your testbench.  `input()` is used to specify RTL sources, and include directories/libraries are specified with `add()`.  The simulator is built with `build()`; when `fast=True`, the simulator binary will not be rebuilt if it already exists.

### Simulator interaction

The basic steps to interact with a simulator are to (1) create a `UmiTxRx` object that points at the switchboard queues used by the DUT, and (2) call the object's `write()` and `read()` to interact with the DUT via UMI.

The `UmiTxRx` constructor accepts two arguments `tx_uri` and `rx_uri`.  Hence, when we write

```python
umi = UmiTxRx('to_rtl.q', 'from_rtl.q')
```

this means, "send UMI packets to the queue called `to_rtl.q`, and receive UMI packets from the queue called `from_rtl.q`".  This matches up with the way that these queues were defined in [testbench.sv](testbench.sv), since the DUT is expecting to receive UMI packets from `to_rtl.q` and send them to `from_rtl.q`.

#### write()

The interface of the `write()` command is `write(addr, data)`, where
* `addr` is a 64-bit UMI address
* `data` is a numpy scalar or array.  For example, `data` could be `np.uint32(0xDEADBEEF)` or `np.arange(64, dtype=np.uint8)`.

The numpy data type determines the `SIZE` for the UMI transaction (e.g., `0` for `np.uint8`, `1` for `np.uint16`, etc.).  The `LEN` for a UMI transaction is `0` for a scalar, and `len(data)-1` for an array.  If `data` is more than 32B (the data bus width provided by `umi_to_queue_sim` and `queue_to_umi_sim`), multiple UMI transactions will automatically be generated within the `write()` command.  This means that you are generally free to write arbitrary binary blobs, without having to worry about bus widths.

#### read()

The interface for `read()` is `read(addr, num_or_dtype, [dtype])`, where
* `addr` is a 64-bit UMI address
* `num_or_dtype` is either an integer or a numpy data type.
* `dtype` is an optional argument that only comes into play if `num_or_dtype` is an integer.  It defaults to `np.uint8`

If `num_or_dtype` is an integer, it means the number of words that should be read starting at `addr`.  The optional argument `dtype` specifies the word size.  For example, `read(0x10, 4)` means "read four bytes starting at 0x10", and `read(0x20, 2, np.uint16)` means "read two uint16s starting at address 0x20".  The result returned will be a numpy array with data type `dtype`.

As with the `write()` command, switchboard will automatically calculate `LEN` and `SIZE` based on the number of element and datatype, and will use multiple reads if necessary.

If `num_or_dtype` is a data type, then a single word of that data type will be read and returned as a scalar.  For example, `read(0x30, np.uint32)` means "read a uint32 from address 0x30".

#### Other commands

The `UmiTxRx` object provides other methods for interaction over UMI, such as `atomic()`.  This will be covered in a future tutorial.

#### fresh=True

You may have noticed the option `fresh=True` when creating the `UmiTxRx` object.  switchboard queues are not automatically deleted at the end of a simulation, so it's important to make sure that any old queues are cleared out before launching a new simulation.  The option `fresh=True` does this; the only rule is that `UmiTxRx` objects must be created before launching a simulation.  At some point, `fresh=True` will be made the default (it's not at the moment for backwards-compatibility reasons).

## Makefile

The `Makefile` is a simple convenience wrapper over the Python script.  You may also notice that `test.py` can be invoked with `make cpp`, which demonstrates switchboard's C++ interface.  That interface will be the subject of a future tutorial.
