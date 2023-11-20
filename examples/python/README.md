# python example

This example shows how to interact with RTL code from Python using switchboard; it's essentially a Python implementation of the [minimal](../minimal) example.  The Python code sends a switchboard packet containing a number to RTL, which increments the number and sends it back to the Python code in a new switchboard packet.  To run the example, type `make`.  You'll see a Verilator build, followed by output like this:

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
```

Looking at the [test.py](test.py) Python code, the outbound switchboard connection is created as an instance of `PySbTx`, and the outbound packet is sent with `PySbTx.send()` (defaults to a blocking send).  The packet itself is an `PySbPacket` object.  In the [testbench.sv](testbench.sv) RTL code, this packet is received by an instance of the `queue_to_sb_sim` module.  The data payload is incremented and assigned to a new switchboard packet, which is transmitted back to Python code with an instance of the `sb_to_queue_sim` module.  The Python code receives that packet via the `PySbRx.recv()` method (which also defaults to a blocking mode of operation).
