# umi_fifo example

`umi_fifo` is a module that implements a FIFO for [SUMI packets](https://github.com/zeroasiccorp/umi#4-signal-umi-layer-sumi) that can be used for buffering in a UMI-based system.  This example shows how to use switchboard to send a stream of random SUMI packets into the `umi_fifo` while reading packets out of the FIFO and verifying that the sequence of packets sent out matches the sequence of packets sent in.

Assuming that `switchboard` is installed in your current Python environment, you can run the example with `./test.py`.  The output will look like this:
```text
...
* TX *
opcode: UMI_REQ_POSTED
dstaddr: 0x25de24da84c70740
size: 3
len: 1
eom: 1
eof: 1
data: [0x89cce9686d531664, 0x684cb99843c6232]
* RX *
opcode: UMI_REQ_WRITE
dstaddr: 0xfefd2a9ed38f9c0c
srcaddr: 0x9158589f508e47b4
size: 2
len: 0
eom: 1
eof: 1
data: [0x90f64317]
...
```

With reference to [test.py](test.py), the interaction is set up as a loop where:
1. A random SUMI packet is generated.
2. We attempt to send that packet into the FIFO (which may fail if the FIFO is full)
3. We attempt to read a packet from the FIFO (which may fail if the FIFO is empty)

This example highlights some convenient features of switchboard for lower-level testing:

1. A random SUMI packet can be generated with the `random_umi_packet()` function, which can be imported directly from the `switchboard` package.  Various optional arguments can be used to constrain the random packet generation.  For example, `random_umi_packet(size=0)` will generate only packets with `SIZE=0` (i.e., 8-bit payload), while `random_umi_packet(size=[1, 2])` will generate only packets with 16- and 32-bit payloads.  The datatype returned by `random_umi_packet()` is `PyUmiPacket`.
2. The `UmiTxRx.send()` method sends a single `PyUmiPacket` through a switchboard connection.  When `blocking=False`, switchboard will return immediately if the connection can't accept the packet and return `False`, rather than blocking until the packet can be sent.
3. The `UmiTxRx.recv()` method receives a single `PyUmiPacket` from a switchboard connection.  When `blocking=False`, switchboard will return `None` immediately if there isn't a packet, rather than blocking until there is.
4. The `==` and `!=` operators can be used to compare `PyUmiPacket` objects.

