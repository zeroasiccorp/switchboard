# tcp example

This example shows how to bridge a switchboard connection using TCP.  This can be useful in situations where a simulation is being run on a remote machine, but a user wants to interact with the simulation from their local machine.  The problem is that switchboard queues are implemented in shared memory, which only applies to processes and hardware connected to a single machine.  switchboard's TCP bridging addresses this problem by creating a shared memory queue on each side of the TCP connection; code running on both sides can then interact with a queue without having to know that the connection is being made over TCP.

To run the example, type `make`.  You'll see output like this:

```text
Wrote addr=0x10 data=0xdeadbeef
Read addr=0x10 data=0xdeadbeef
```

Delving into [test.py](test.py), you'll see that the script launches two scripts, [ram/ram.py] and [fifos/fifos.py].  These run switchboard simulations for a UMI RAM module and UMI FIFO module, respectively.  The `test.py` script connects to the FIFO simulation via TCP, using `SbNetwork.external()` with one of the arguments set to `TcpIntf` to represent a TCP port.  `SbNetwork.simulate()` is called even though there is no RTL being simulated at the top level, since this is also where TCP bridges are launched.

In the scripts `ram.py` and `fifos.py`, RTL simulations are specified using `SbNetwork`, with `SbNetwork.connect()` and `SbNetwork.external()` used to specify interactions with switchboard connections being bridged over TCP.
