# Switchboard

[![Actions Status](https://github.com/zeroasiccorp/switchboard/actions/workflows/regression.yml/badge.svg?branch=main)](https://github.com/zeroasiccorp/switchboard/actions)

Switchboard is a framework for packet communication between distinct hardware models, such as RTL simulations, RTL implemented on FPGAs, and fast SW models.  This makes it possible to simulate large hardware systems in a distributed fashion, using whatever models are available for the different components.

In such a simulation, each hardware model has one or more SB ports.  Each is unidirectional: it may act as an input or an output, but not both.  In addition, each SB connection is single-producer, single-consumer (SPSC): an output port may not drive more than one input port, and an input port may not be driven by more than one output port.

Here's an example of what a Switchboard connection topology might look like:

...

Note that topologies are not constrained to be in a grid, and there is no specific number of Switchboard ports that must be on a given model.  Our project [griddle](https://github.com/zeroasiccorp/griddle) is a layer that sits above Switchboard, providing a grid-specific abstraction.

The method for adding a Switchboard port depends on the language that a HW model is implemented in.  For RTL-based models, SB ports are instantiated as Verilog models, whereas for C++ and Python-based models, these ports are instantiated as objects.  In all cases, however, communication happens through shared-memory queues, where an SB output port is driving packets into the queue, and an SB input port is reading from that queue.  This standardization is what allows any two kinds of models to talk to each other.

A shared-memory SPSC queue is an appealing common interface because it is one of the fastest interprocess communication techniques, with latencies on the order of hundreds of nanoseconds; no system calls are required to transmit and receive data.  At the same time, this type of queue is straightforward to implement for FPGA platforms, with queue read and write operations only requiring a handful of memory transactions.

## Installation

Clone the repository, change to its directory, and initialize its submodules:

```shell
> git clone https://github.com/zeroasiccorp/switchboard.git
> cd switchboard
> git submodule update --init --recursive
```

Then install the Switchboard Python package using `pip` (recommended to do this in a contained environment such as a virtual environment, conda environment, etc.)

```shell
> pip install --upgrade pip
> pip install -e .
```

This will install `pybind11` if necessary and build a Python binding to the underlying C++ library.

## Example

Various examples demonstrating the features of Switchboard are in the `examples` folder.  A good starting point is the `python` example, where a Python script sends packets to and receives packets from a Verilator RTL simulation.  The configuration is simple: there is a small RTL simulation that accepts an SB packet, adds one to its value, and transmits the result on its SB output port.  On the other side, a Python script sends an SB packet to the simulation, and checks that the packet it gets back has been incremented.

To run this example, you'll need `verilator` (`sudo apt install verilator` for Ubuntu, `brew install verilator` for macOS).  You can then run the example by changing directory to `examples/python` and then typing `make`.  That should produce output like the following:

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

To get a sense of how this works, open the Python script `switchboard/examples/python/scripts/test.py`.  The core logic is essentially:

```python
from switchboard import PySbPacket, PySbTx, PySbRx
...
tx = PySbTx("queue-5555")
rx = PySbRx("queue-5556")
...
txp = PySbPacket(...)
tx.send(txp)
...
rxp = rx.recv()
```

In other words, we create an SB output port (`tx`) and an SB input port (`rx`).  An SB packet is then created (`txp`) and sent via the output port.  Finally, a new SB packet is received from the input port.

To get a sense of how Switchboard is used in RTL, have a look at the Verilog part of this example in `switchboard/examples/python/verilog/testbench.sv`.  The core logic is the instantiation of `sb_rx_sim` (SB input port) and `sb_tx_sim` (SB output port), along with the initialization step to define the name of each SB connection.  Notice that the Python output port is matched to the Verilog input port (`queue-5555`) and similarly the Python input port is matched to the Verilog output port (`queue-5556`).

```verilog
// ...

sb_rx_sim rx_i (
    .clk(clk),
    .data(sb_rx_data),
    .dest(sb_rx_dest),
    .last(sb_rx_last),
    .ready(sb_rx_ready),
    .valid(sb_rx_valid)
);

sb_tx_sim tx_i (
    .clk(clk),
    .data(sb_tx_data),
    .dest(sb_tx_dest),
    .last(sb_tx_last),
    .ready(sb_tx_ready),
    .valid(sb_tx_valid)
);

// ...

initial begin
    rx_i.init("queue-5555");
    tx_i.init("queue-5556");
end

// ...
```

Using the same name for two ports is what establishes a connection between them.  You can use any name that you like for a SB connection, as long as it is a valid file name.  The reason is that SB connections are visible as files on your file system.  So after this example runs, it will leave behind files called `queue-5555` and `queue-5556`.  It's convenient to name SB connections in a way that is amenable to pattern matching, so that you can do things like `rm queue-*` to clean up old connections.

We encourage you to explore the other examples, which demonstrate simulation with Icarus Verilog (`minimal-icarus`), Switchboard's C++ library (`minimal`), bridging SB connections via TCP (`tcp`), and Switchboard's UMI abstraction (`umiram_python`).  There is also a more involved example showing how Switchboard can be used to construct a grid of PicoRV32 processors, each running in a separate Verilator simulation (`riscv-grid`).

## Packet format

At this point, you may be wondering what exactly a SB packet is, so we'll address that in this section.

An SB packet is a simple data structure with three parts:
1. A 32-bit `destination`.
2. A 32-bit `flags` bit vector.  Currently only bit "0" is used, providing the `last` flag.
3. A 256-bit data payload.

The most important part of the packet is the data payload.  That's the information that is being conveyed from one place to another; it's what we were talking about when we said that a packet was being incremented in the `python` example.

The two other parts, `destination` and `flags`, control how the packet is routed.  `destination` indicates the intended recipient of the packet as a flat, unsigned 32-bit integer.  This provides a mechanism where a packet can be routed through multiple hops before reaching its final destination.

For example, consider using Switchboard to build a simple topology in which packets can be sent from one HW block to one of two other blocks.  One could indicate which block should receive the packet using the `destination` field, with a router transmitting the packet to the right one.

...

The `last` indicator (part of the `flags` bit vector) indicates whether there is more to come as part of a transaction.  The rule is that a transmission cannot be interrupted as long as as `last` is zero.  As an example, consider the system below, where Block A and Block B are both sending SB packets to the same port on Block C, using a router to multiplex between the two.  Following the rule of unbroken transmissions, if the router starts sending a sequence of packets from Block A to Block C, it cannot switch to sending packets from Block B to Block C until it gets a packet from Block A that hast `last` set to one.  It is legal to have `last=1` set in all packets, meaning that packets can be interspersed at any time.

...

The purpose of `last` is two-fold.  For one, it simplifies the process of transmitting "burstable" protocols such as UMI through Switchboard.  It also provides opportunities for performance optimization.  For example, if a long sequence of SB packets is being sent over TCP, the TCP bridge knows it can wait to fill up its transmission buffer as long as `last=0`.  Without the `last` bit, the bridge would have to send each packet one at a time (or wait a predefined time for more packets), since any given packet may be the last one.
