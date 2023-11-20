# tcp example

This example shows how to bridge a switchboard connection using TCP.  This can be useful in situations where a simulation is being run on a remote machine, but a user wants to interact with the simulation from their local machine.  The problem is that switchboard queues are implemented in shared memory, which only applies to processes and hardware connected to a single machine.  switchboard's TCP bridging addresses this problem by creating a shared memory queue on each side of the TCP connection; code running on both sides can then interact with a queue without having to know that the connection is being made over TCP.

To run the example, type `make`.  You'll see output like this:

```text
*** TX packet ***
dest: 123456789
last: 1
data: [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31]

*** RX packet ***
dest: 123456789
last: 1
data: [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31]
```

Delving into [test.py](test.py), you'll see that the code is similar to the [python](../python) example, using `PySbTx` and `PySbRx` objects and the `send()` and `recv()` methods.  The difference is that `PySbTx` and `PySbRx` are two sides of the same connection, but use different queue names (`tx.q` and `rx.q`).  We launch two TCP bridge processes, one for each side of the connection, using `start_tcp_bridge()`.  It must be the case that one side is the server and one side is the client, but it doesn't matter which one is which, and the launch order doesn't matter either.  However, when bridging between two different machines, the client side must specify the IP address of the server in the `host` argument of `start_tcp_bridge()`.  Also, if you're running multiple bridges simultaneously, you'll need to specify the `port` argument for each bridge to make sure that they don't interfere with each other.
