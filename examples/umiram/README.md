# umiram tutorial

Switchboard provides a Python interface for reading from and writing to RTL designs using UMI.  This tutorial shows how to create such a setup, using a simple UMI memory design as an example.  You'll learn how to instantiate switchboard Verilog modules that connect to the DUT, and how to interact with the DUT from Python.

## Installation

If you haven't already cloned this repo and installed the switchboard Python package, please do that first.  We recommend installing switchboard in a virtual env, conda env, etc. to keep things tidy.

```shell
> git clone https://github.com/zeroasiccorp/switchboard.git
> cd switchboard
> git submodule update --init --recursive
> pip install --upgrade pip
> pip install -e .
```

## Structure

The RTL structure of this example is a Verilog module, `testbench` (`testbench.sv`), that instantiates UMI memory, `umiram` (`../common/verilog/umiram.sv`).  Within `testbench`, the UMI `udev_req` and `udev_resp` ports of `umiram` are terminated using the `umi_rx_sim` and `umi_tx_sim` modules provided by switchboard.

A Verilator simulation is built using `testbench` as the top level.  When it runs, UMI packets flow into `udev_req` from a switchboard queue, `client2rtl.q`, and flow out from `udev_resp` into a switchboard queue, `rtl2client.q`.  These queues will show up on your computer as ordinary files, each representing a region of shared memory.

In the Python script `test.py`, a UMI driver is instantiated that sends packets to `client2rtl.q` and receives them from `rtl2client.q`.  `write()` and `read()` methods provided by the driver allow numpy arrays and scalars to be written to and read from the DUT, with each operation mapping to one or more UMI operations with automatically calculated `SIZE` and `LEN` parameters.

<img width="561" alt="image" src="https://github.com/zeroasiccorp/switchboard/assets/19254098/4330f9fb-5313-48c0-9d05-4ff315269477">

These operations are automated in this example with a Makefile.  If you haven't already, `cd` into this folder, and then run `make`.  You should see the following output, after the Verilator build completes:

```text
$ make
...
### WRITES ###
### READS ###
Read: 0xbaadf00d
Read: 0xb0bacafe
Read: 0xdeadbeef
Read: 0xbaadd00dcafeface
```

In the sections that follow, we'll go into the different components of this example, to give a sense of how they might be modified for your own use.

## testbench.sv

The main purpose of the top-level module, `testbench`, is to instantiate the DUT and connect its UMI ports to switchboard-provided "end caps": `umi_rx_sim` and `umi_tx_sim`.  `umi_rx_sim` receives UMI packets from outside of the Verilog simulation and drives them into the DUT, while `umi_tx_sim` drives UMI packets to the outside world that are provided by the DUT.  As you can see in the file, there is a one-to-one mapping of all interface pins on these modules to signals on the DUT.

```verilog
umi_rx_sim rx_i (
    .clk(clk),
    .data(udev_req_data),
    .srcaddr(udev_req_srcaddr),
    .dstaddr(udev_req_dstaddr),
    .cmd(udev_req_cmd),
    .ready(udev_req_ready),
    .valid(udev_req_valid)
);
umi_tx_sim tx_i (
    .clk(clk),
    .data(udev_resp_data),
    .srcaddr(udev_resp_srcaddr),
    .dstaddr(udev_resp_dstaddr),
    .cmd(udev_resp_cmd),
    .ready(udev_resp_ready),
    .valid(udev_resp_valid)
);
```

Although only one TX and one RX end cap are used in this example, switchboard supports instantiating multiple end caps of each type in a single simulation.

Another important part of `testbench.sv` are the lines where these end caps are assigned switchboard queue names:

```verilog
initial begin
    /* verilator lint_off IGNOREDRETURN */
    rx_i.init("client2rtl.q");
    tx_i.init("rtl2client.q");
    /* verilator lint_on IGNOREDRETURN */
end
```

There is nothing special about these names; they can be any legal file name.  The main important thing is that the names used match up to the names used in the SW driver.  For example, since the DUT is expecting to receive UMI packets from `client2rtl.q`, the Python script should be configured to send packets to `client2rtl.q`.  The switchboard queues are ordinary files, and they may stick around after a simulation - for that reason, you may want to give them a globbable name so you can do things like `rm *.q`, or add `*.q` to `.gitignore`.

In looking through `testbench.sv`, you may haved noticed that `umi_rx_sim` has a parameter called `VALID_MODE_DEFAULT`, and `umi_tx_sim` has a parameter called `READY_MODE_DEFAULT`.  These control the ready/valid signaling style used by the switchboard modules.  All of the styles are legal in terms of the UMI specification, but can help catch different kinds of hardware bugs.

* `VALID_MODE_DEFAULT` on `umi_rx_sim`
    * `0` means to always set `valid` to `0` after completing a transaction.  This means that if there is a steady stream of data being driven out and `ready` is kept asserted, `valid` will alternate between `0` and `1`.
    * `1` means to try to keep `valid` asserted as much as possible, so if there is a constant stream of data being driven out and `ready` is kept asserted, `valid` will remain asserted.
    * `2` means to flip a coin before deciding to drive out the next packet.  This causes the `valid` line to have a random pattern if there is a constant stream of data to be driven and `ready` is kept asserted.
* `READY_MODE_DEFAULT` on `umi_tx_sim`
    * `0` means to hold off on asserting `ready` until `valid` has been asserted.
    * `1` means to assert `ready` as much as possible, so if `valid` is held high, `ready` will remain asserted as long as more packets can be pushed into the switchboard queue (i.e., as long as the SW driver isn't backpressuring)
    * `2` means to flip a coin on each cycle to determine if `ready` will be asserted in that cycle (provided that there is room in the switchboard queue)

## Makefile

When you type `make`, two actions take place: first, a Verilator simulator is built, resulting in the binary `obj_dir/Vtestbench`, and second, the Python script `test.py` is run.  Building the Verilator simulator requires a few switchboard-specific lines:

* `SBDIR := $(shell switchboard --path)`
    * Creates a variable pointing to the installation directory of switchboard.  For convenience, this is provided by the `switchboard` command, which was installed when you pip-installed this repo.  You can try running `switchboard --path` at the command line to verify its behavior.
* `$(SBDIR)/dpi/switchboard_dpi.cc`
    * Under the hood, switchboard uses DPI to implement `umi_rx_sim` and `umi_tx_sim` (VPI is used for Icarus Verilog).
    * This file needs to be added to the source file list for Verilator so that it knows where to find the DPI implementation.
* `-y $(SBDIR)/verilog/sim`
    * Lets Verilator know about the folder containing `umi_rx_sim` and `umi_tx_sim`, so that you can use them in `testbench.sv` without having to include them explicitly in the source file list.
* `-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp"`
    * Tells Verilator to use these options when compiling the simulator.  `-I$(SBDIR)/cpp` is needed because `$(SBDIR)/dpi/switchboard_dpi.cc` includes a file from that path.
    * `-Wno-unknown-warning-option` is a convenience for macOS users, and is likely not switchboard-specific.
* `-LDFLAGS "-pthread"`
    * Also needed by `$(SBDIR)/dpi/switchboard_dpi.cc`

You may also notice that `test.py` can be invoked with either `make cpp`, which demonstrates switchboard's C++ interface.  That interface will be the subject of a future tutorial.


## test.py

This is the Python script that interacts with a running RTL simulation of `umiram`.  The basic steps to do this are to (1) create a `UmiTxRx` object that points at the switchboard queues used by the DUT, and (2) call the object's `write()` and `read()` to interact with the DUT via UMI.

The `UmiTxRx` constructor accepts two arguments `tx_uri` and `rx_uri`.  Hence, when we write

```python
umi = UmiTxRx(client2rtl, rtl2client)
```

this means, "send UMI packets to the queue called `client2rtl`, and receive UMI packets from the queue called `rtl2client`".  This matches up well with the way that these queues were defined in `testbench.sv`, since the DUT is expecting to receive UMI packets from `client2rtl` and send them to `rtl2client`.

### write()

The interface of the `write()` command is `write(addr, data)`, where
* `addr` is a 64-bit UMI address
* `data` is a numpy scalar or array.  For example, `data` could be `np.uint32(0xDEADBEEF)` or `np.arange(64, dtype=np.uint8)`.

The numpy data type determines the `SIZE` for the UMI transaction (e.g., `0` for `np.uint8`, `1` for `np.uint16`, etc.).  The `LEN` for a UMI transaction is `0` for a scalar, and `len(data)-1` for an array.  If `data` is more than 32B (the data bus width provided by `umi_tx_sim` and `umi_rx_sim`), multiple UMI transactions will automatically be generated within the `write()` command.  This means that you are generally free to write arbitrary binary blobs, without having to worry about bus widths.

### read()

The interface for `read()` is `read(addr, num_or_dtype, [dtype])`, where
* `addr` is a 64-bit UMI address
* `num_or_dtype` is either a integer or a numpy data type.
* `dtype` is an optional argument that only comes into play if `num_or_dtype` is an integer.  It defaults to `np.uint8`

If `num_or_dtype` is an integer, it means the number of words that should be read starting at `addr`.  The optional argument `dtype` specifies the word size.  For example, `read(0x10, 4)` means "read four bytes starting at 0x10", and `read(0x20, 2, np.uint16)` means "read two uint16s starting at address 0x20".  The result returned will be a numpy array with data type `dtype`.

As with the `write()` command, switchboard will automatically calculate `LEN` and `SIZE` based on the number of element and datatype, and will use multiple reads if necessary.

If `num_or_dtype` is a data type, then a single word of that data type will be read and returned as a scalar.  For example, `read(0x30, np.uint32)` means "read a uint32 from address 0x30".

### Other commands

The `UmiTxRx` object provides other methods for interaction over UMI, such as `atomic()`.  This will be covered in a future tutorial.

### delete_queue()

You may have noticed the lines

```python
for q in [client2rtl, rtl2client]:
    delete_queue(q)
```

near the top of `test.py`.  switchboard queues are not automatically deleted, so it's important to make sure that any old queues are cleared out before launching a new simulation.  Sometimes it is convenient to auto-delete queues as part of the teardown process for a verification environment.
