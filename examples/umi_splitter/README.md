# umi_splitter example

`umi_splitter` is a module from the [UMI repository](https://github.com/zeroasiccorp/umi) has one SUMI input port and two SUMI output ports.  Incoming SUMI packets are routed to one of the two outputs depending on whether they are a UMI request or a UMI response.  This example shows how to use switchboard to send a stream of random SUMI packets into the `umi_splitter` module while receiving packets from both outputs and verifying that packets have been routed appropriately.

Assuming that `switchboard` is installed in your current Python environment, you can run the example with `./test.py`.  The output will look like this:
```text
* IN *
opcode: UMI_REQ_WRITE
dstaddr: 0x7ad8961f2d2b57b2
srcaddr: 0x87ca3bbd232244ae
size: 1
len: c
eom: 1
eof: 1
data: [0x5df3, 0xcab6, 0xdf6f, 0x414f, 0xfa85, 0xfd0a, 0xe046, 0x725a, 0xf71d, 0x3164, 0xcf1, 0x40c8, 0xd15f]
...
* OUT #1 *
opcode: UMI_REQ_WRITE
dstaddr: 0x1763c3150f8c990e
srcaddr: 0x5b38c31348dfe4a6
size: 1
len: 3
eom: 1
eof: 1
data: [0xfecf, 0xb865, 0x786e, 0x7716]
```

With reference to [test.py](test.py), the interaction is set up as a loop where:
1. A random SUMI packet is generated.
2. We attempt to send that packet into the splitter
3. We attempt to receive a SUMI packet from each of the splitter outputs

After sending a receiving a certain number of packets, the lists of packets sent vs. packets received from both splitter outputs are compared to make sure that the splitter is operating correctly.  The switchboard features used to implement this test are similar to those used in the [umi_fifo example](../umi_fifo), so we won't explain them here.  The main difference is that we check the LSB of the 32-bit [cmd signal](https://github.com/zeroasiccorp/umi#323-message-types) of each random packet to determine which output port we expect it to be routed to.
