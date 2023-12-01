# Switchboard

[![Actions Status](https://github.com/zeroasiccorp/switchboard/actions/workflows/regression.yml/badge.svg?branch=main)](https://github.com/zeroasiccorp/switchboard/actions)
[![Documentation Status](https://github.com/zeroasiccorp/switchboard/actions/workflows/documentation.yml/badge.svg?branch=main)](https://zeroasiccorp.github.io/switchboard/)

Switchboard (SB) is a framework for communication between distinct hardware models, such as RTL simulations, RTL implemented on FPGAs, and fast SW models.  This makes it possible to simulate large hardware systems in a distributed fashion, using whatever models are available for the different components.

In such a simulation, each hardware model has one or more SB ports.  Each is unidirectional: it may act as an input or an output, but not both.  In addition, each SB connection is single-producer, single-consumer (SPSC): an output port may not drive more than one input port, and an input port may not be driven by more than one output port.

Here's an example of what a switchboard connection topology might look like:

<img width="318" alt="image" src="https://user-images.githubusercontent.com/19254098/225485548-ff127b2e-d959-46c0-af1d-2c4bbe3f119d.png">

The method for adding a switchboard port depends on the language that a HW model is implemented in.  For RTL-based models, SB ports are instantiated as Verilog models, whereas for C++ and Python-based models, these ports are instantiated as objects.  We provide both a low-level interface for moving data directly between SB ports, as well as a higher-level interface for running [UMI](https://github.com/zeroasiccorp/umi) transactions over SB connections.

Under the hood, communication happens through shared-memory queues, where an SB output port is driving packets into the queue, and an SB input port is reading from that queue.  This standardization is what allows any two kinds of models to talk to each other.  A shared-memory SPSC queue is an appealing common interface because it is one of the fastest interprocess communication techniques, with latencies on the order of hundreds of nanoseconds; no system calls are required to transmit and receive data.  At the same time, this type of queue is straightforward to implement for FPGA platforms, with queue read and write operations only requiring a handful of memory transactions.


## Installation

This package is directly installable with pip.  We recommended installation in a contained environment such as a virtual environment, conda environment, etc.

```shell
$ pip install --upgrade pip
$ pip install git+https://github.com/zeroasiccorp/switchboard.git
```

If you're a switchboard developer, or want to run the examples below, we instead recommend cloning the repo and installing it in-place (`-e`).

```shell
$ git clone https://github.com/zeroasiccorp/switchboard.git
$ cd switchboard
$ git submodule update --init
$ pip install --upgrade pip
$ pip install -e .
```

To run the examples below, first run the following command:

```
$ ./examples/get_deps.py
```

This clones some additional repositories that are needed by the examples, but are not needed if you only want to use the switchboard Python package.


## Example

Various examples demonstrating the features of switchboard are in the [examples](examples) folder.  A good starting point is the [python](examples/python) example, where a Python script sends packets to and receives packets from a Verilator RTL simulation.  The configuration is simple: there is a small RTL simulation that accepts an SB packet, increments the data payload, and transmits the result on its SB output port.  On the other side, a Python script sends an SB packet to the simulation, and checks that the packet it gets back has been incremented.

<img width="311" alt="image" src="https://user-images.githubusercontent.com/19254098/225485672-1793521d-a9db-4c18-ad61-c22a605f8720.png">

To run this example, you'll need `verilator` (`sudo apt install verilator` for Ubuntu, `brew install verilator` for macOS).  You can then run the example by changing directory to [examples/python](examples/python) and then typing `make`.  That should produce output similar to the following:

```text
*** TX packet ***
dest: 123456789
last: 1
data: [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31]

*** RX packet ***
dest: 123456789
last: 1
data: [ 1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
 25 26 27 28 29 30 31 32]

- ../verilog/testbench.sv:72: Verilog $finish
PASS!
```

To get a sense of how this works, open the Python script [examples/python/test.py](examples/python/test.py).  The core logic is essentially:

```python
from switchboard import PySbPacket, PySbTx, PySbRx
...
tx = PySbTx("to_rtl.q")
rx = PySbRx("from_rtl.q")
...
txp = PySbPacket(...)
tx.send(txp)
...
rxp = rx.recv()
```

In other words, we create an SB output port (`tx`) and an SB input port (`rx`).  An SB packet is then created (`txp`) and sent via the output port.  Finally, a new SB packet is received from the input port.

To get a sense of how switchboard is used in RTL, have a look at the Verilog part of this example in [examples/python/testbench.sv](examples/python/testbench.sv).  The core logic is the instantiation of `queue_to_sb_sim` (SB input port) and `sb_to_queue_sim` (SB output port), along with the initialization step to define the name of each SB connection.  Notice that the Python output port is matched to the Verilog input port (`to_rtl.q`) and similarly the Python input port is matched to the Verilog output port (`from_rtl.q`).

```verilog
// ...

queue_to_sb_sim rx_i (
    .clk(clk),
    .data(sb_rx_data),
    .dest(sb_rx_dest),
    .last(sb_rx_last),
    .ready(sb_rx_ready),
    .valid(sb_rx_valid)
);

sb_to_queue_sim tx_i (
    .clk(clk),
    .data(sb_tx_data),
    .dest(sb_tx_dest),
    .last(sb_tx_last),
    .ready(sb_tx_ready),
    .valid(sb_tx_valid)
);

// ...

initial begin
    rx_i.init("to_rtl.q");
    tx_i.init("from_rtl.q");
end

// ...
```

Using the same name for two ports is what establishes a connection between them.  You can use any name that you like for a SB connection, as long as it is a valid file name.  The reason is that SB connections are visible as files on your file system.  After this example runs, it will leave behind files called `to_rtl.q` and `from_rtl.q`.  It's convenient to name SB connections in a way that is amenable to pattern matching, so that you can do things like `rm *.q` to clean up old connections.

We encourage you to explore the other examples, which demonstrate simulation with Icarus Verilog and switchboard's C++ library ([minimal](examples/minimal)), bridging SB connections via TCP ([tcp](examples/tcp)), and switchboard's UMI abstraction ([umiram](examples/umiram)).


## Build automation

We also provide build automation powered by [SiliconCompiler](https://github.com/siliconcompiler/siliconcompiler) that makes it easy to build RTL simulations with switchboard infrastructure (`queue_to_sb_sim`, `sb_to_queue_sim`, etc.).  This is mainly important because Verilog DPI and VPI are used under the hood, requiring certain flags to be passed to the RTL simulator during the build.  Using our build automation lets you focus on specifying RTL sources, without having to deal with these details.

As an example, we return to [examples/python](examples/python).  The basic logic for a Verilator build is:

```python
from switchboard import SbDut

dut = SbDut('name-of-top-level-module', default_main=True)

dut.input('path/to/file/1')
dut.input('path/to/file/2')
...

dut.build()

dut.simulate()
```

In other words, create an `SbDut` object, `input()` files, `build()` it to compile the Verilator simulator, and use `simulate()` to start the simulator.  `SbDut` is a subclass of `siliconcompiler.Chip`, which allows you to invoke a range of features to control the simulator build, such as specifying include paths and `` `define `` macros.  More information about `siliconcompiler.Chip` can be found [here](https://docs.siliconcompiler.com/en/stable/reference_manual/core_api.html#siliconcompiler.core.Chip).


## Packet format

An SB packet is a simple data structure with three parts, defined in [switchboard/cpp/switchboard.hpp](switchboard/cpp/switchboard.hpp).
1. A 32-bit `destination`.
2. A 32-bit `flags` bit vector.  Currently only bit "0" is used, providing the `last` flag.
3. A 416-bit data payload.  This width was chosen to accommodate a UMI packet with a 256 bit payload, 64-bit source and destination addresses, and a 32-bit command.  In the future, we may support parameterizable data widths for switchboard connections.

`destination` and `flags` control how the packet is routed.  `destination` indicates the intended recipient of the packet as a flat, unsigned 32-bit integer.  This provides a mechanism where a packet can be routed through multiple hops before reaching its final destination.

For example, consider using switchboard to build a simple topology in which packets can be sent from one HW block to one of two other blocks.  One could indicate which block should receive the packet using the `destination` field, with a router transmitting the packet to the right one.

<img width="291" alt="image" src="https://user-images.githubusercontent.com/19254098/225485726-60ce5539-f282-4ceb-8e33-6cb2b7220ffd.png">

The `last` indicator (part of the `flags` bit vector) indicates whether there is more to come as part of a transaction.  The rule is that a transmission cannot be interrupted as long as as `last` is zero.  As an example, consider the system below, where Block A and Block B are both sending SB packets to the same port on Block C, using a router to multiplex between the two.  Following the rule of unbroken transmissions, if the router starts sending a sequence of packets from Block A to Block C, it cannot switch to sending packets from Block B to Block C until it gets a packet from Block A that has `last` set to one.  It is legal to have `last=1` set in all packets, meaning that packets can be interspersed at any time.

<img width="253" alt="image" src="https://user-images.githubusercontent.com/19254098/225485752-59cd02f3-6877-4cbd-960c-823276d8a815.png">

The purpose of `last` is two-fold.  For one, it simplifies the process of transmitting "burstable" protocols such as UMI through switchboard.  It also provides opportunities for performance optimization.  For example, if a long sequence of SB packets is being sent over TCP, the TCP bridge knows it can wait to fill up its transmission buffer as long as `last=0`.  Without the `last` bit, the bridge would have to send each packet one at a time (or speculatively wait for more packets), since any given packet may be the last one.


## UMI interface

In addition to supporting data movement directly through SB packets, we provide a higher-level interface for running [UMI](https://github.com/zeroasiccorp/umi) transactions over switchboard connections.  The mechanisms for this can be seen in the `examples/umi*` examples.  Here's a sketch of what UMI transactions look like, adapted from the definition of `python_intf()` in [examples/umiram/test.py](examples/umiram/test.py):

```python
from switchboard import UmiTxRx

umi = UmiTxRx(from_client, to_client, fresh=True)

wrbuf = np.array([elem1, elem2, ...], dtype)
umi.write(wraddr, wrbuf)

rdbuf = umi.read(rdaddr, num, dtype)  # also a numpy array
```

We are no longer creating `PySbTx` and `PySbRx` objects, but rather a single `UmiTxRx` object with two SB ports: `from_client`, and `to_client`.  Transactions are sent by the Python script through the `from_client` port, and responses are received back through the `to_client` port.

UMI write transactions are generated with the `umi.write()` method, which accepts an address and numpy array or scalar as arguments.  This sends out one or more [SUMI](https://github.com/zeroasiccorp/umi#4-signal-umi-layer-sumi) packets to implement the write request, packing the data, source address, destination address, and command into SB packets.  Since an SB packet is 416 bits, and the two addresses + command take up 160 bits, each SB packet contains up to 256b data.  Switchboard automatically splits up larger transactions into multiple SUMI packets as needed, incrementing the source and destination addresses automatically.  Optional arguments to `write()` control where a ack'd or non-ack'd (posted) write is used and the maximum amount of data to send in a single SUMI packet.  If an ack'd write is used, `write()` blocks until the response is received.

In a similar fashion, `umi.read()` reads a certain number of words from a given address.  For example, `umi.read(0x1234, 4, np.uint16)` will send out a UMI read request with `dstaddr=0x1234`, `LEN=3`, `SIZE=1` from the SB port `from_client`.  When it gets the response to that query on `to_client`, it will return an array of 4 `np.uint16` words to the Python script.  A `umi.atomic()` method is also provided to generate UMI atomic transactions.

Sometimes it is convenient to work directly with SUMI packets, for example when testing a UMI FIFO or UMI router.  For that situation, we provide `send()` and `recv()` methods for `UmiTxRx`, highlighted in [examples/umi_fifo/test.py](examples/umi_fifo/test.py).  In that exampe, we are sending SUMI packets into a UMI FIFO, and want to make sure that the sequence of packets read out of the FIFO is the same as the sequence of packets written in.

The main `while` loop is essentially:

```python
txq = []

while ...:
    txp = random_umi_packet()
    if umi.send(txp, blocking=False):
        txq.append(txp)

    rxp = umi.recv(blocking=False)
    if rxp is not None:
        assert rxp == txq[0]
        txq.pop(0)
```

In other words, first try to write a random packet into the FIFO.  If successful, add it to the back of a list of outstanding packets.  Then, try to read a packet from the FIFO.  If successful, make sure that the packet is equal to the oldest outstanding packet (since this is a first-in, first-out queue) and remove that outstanding packet from our records.  Continue in a loop until a sufficient number of transactions have been checked.

This code example demonstrates several features:
1. `send()` and `recv()` for working with SUMI packets, represented using `PyUmiPacket` objects.
2. `blocking=False` for non-blocking transactions.  `send()` returns `True` if successful and `False` otherwise; `recv()` returns a `PyUmiPacket` if successful, and `None` otherwise.  A transaction might be unsuccessful if the underlying UMI FIFO is full or empty.  For example, if we don't call `umi.recv()`, eventually the FIFO will fill, and subsequent `send()` invocations will fail (returning `False`).  Similarly, if we keep calling `umi.recv()` without calling `umi.send()`, eventually the FIFO will be empty, and `umi.recv()` will fail (returning `None`).
3. The ability to generate random SUMI packets with `random_umi_packet()`.  Various optional arguments can constrain the opcodes, addresses, and data.
4. `PyUmiPacket` objects can be compared using Python `==` and `!=` operators.  This checks if two packets have equal commands, addresses, and data.


## Queue format

Under the hood, SB ports are implemented using shared memory queues.  The data structure used is made simple enough that RTL running on FPGAs can directly read and write to these queues, without the need for bridge programs.  In fact, if two FPGAs have access to the same memory space, they can communicate through a shared memory queue without any involvement from the host operating system, after the initial setup.

The layout of the queue is:
* Bytes 0-3: head (int32)
* Bytes 64-67: tail (int32)
* Bytes 128-179: SB packet
* Bytes 256-307: SB packet
* Bytes 320-371: SB packet
* ...
* Bytes 4,032-4,095: SB packet

To write an SB packet to the queue, compute `next_head = head + 1`.  If `next_head` equals `62` (the end of the queue), then set `next_head` to `0`.  If `next_head` equals `tail`, then the write fails - the queue is full.  Otherwise, write the SB packet to address `128 + (64 * head)`, and then set `head` to `next_head`.

Reading an SB packet works in a similar fashion.  If `tail` equals `head`, the read fails - the queue is empty.  Otherwise, read the SB packet from address `128 + (64 * tail)`, and then increment `tail`.  If `tail` equals `62` (the end of the queue), then set `tail` to `0`.

The queue implementation in C is in [switchboard/cpp/spsc_queue.h](switchboard/cpp/spsc_queue.h), with care taken to avoid memory ordering hazards, and various cache-oriented optimizations.  The queue implementation in Verilog (intended for FPGA-based emulation) can be found in [switchboard/verilog/fpga/sb_rx_fpga.sv](switchboard/verilog/fpga/sb_rx_fpga.sv) and [switchboard/verilog/fpga/sb_tx_fpga.sv](switchboard/verilog/fpga/sb_tx_fpga.sv).


## License

[Apache 2.0](LICENSE)


## Contributing

switchboard is an open-source project and welcomes contributions. To find out how to contribute to the project, see our
[Contributing Guidelines](CONTRIBUTING.md).


## Issues / Bugs

We use [GitHub Issues](https://github.com/zeroasiccorp/switchboard/issues) for tracking requests and bugs.
