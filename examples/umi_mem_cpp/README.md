# umi_mem_cpp example

This example shows how to create a hardware model using switchboard's C++ library.  The motivation for doing this is speed: HW models implemented in C++ will generally be faster than those using RTL simulation or those written in Python.  This can make a big difference when running large tasks, such as booting Linux on a simulated CPU design.

The hardware being modeled is a UMI memory, implemented in [umi_mem.cc](umi_mem.cc).  From a transaction-level perspective, the behavior of `umi_mem` is very similar to the UMI memory implemented in [umiram.sv](../common/verilog/umiram.sv) for the [umiram example](../umiram).

To run the example, type `make`.  This first compiles the `umi_mem` model, and then exercises that model with the Python stimulus in [test.py](test.py).  The output will look like this:

```text
### MINIMAL EXAMPLE ###
Read: 3735928559
...
### WRITES ###
### READS ###
Read: 0xbaadf00d
...
### ATOMICS ###
* Atomic SWAP, dtype=uint8
Read: 0xc
Atom: 0xc
Read: 0x6a
...
* Atomic MAXU, dtype=uint64
Read: 0xbea555fedd3fd7e1
Atom: 0xbea555fedd3fd7e1
Read: 0xd7d83eda44628e45
```

Since the Python stimulus is very similar to the stimulus in the umiram example, we won't walk through the code here.  One note about the `test_rdma` feature: the `umi_mem` C++ model includes [UMI RDMA](https://github.com/zeroasiccorp/umi#345-req_rdma) support, which is not in the `umiram.sv` RTL model.  As a result, the Python code in this example includes some extra logic to exercise the RDMA feature.

On the C++ side, a UMI request is received directly as a switchboard packet using `SBRX.recv_peek()` (more on that in a moment), and then unpacked into SUMI signals, represented in a `umi_packet` struct.  The fields of the 32-bit [cmd signal](https://github.com/zeroasiccorp/umi#323-message-types) are read out using functions prefixed with `umi_`.  For example, the `LEN` field is read with `umi_len(cmd)` and the `SIZE` field is read with `umi_size(cmd)`.

After interpreting the request encoded in the `cmd` signal, the model implements the request, sending back a response if needed.  For example, if `cmd` contains `REQ_WR`, the model sends back `RESP_WR` to the `srcaddr` given in the request.  The response `cmd` field is formatted using `umi_pack()`, and that field is packed into a switchboard packet, along with the response `dstaddr` and `data` fields, using `SBTX.send()`.

Returning to `SBRX.recv_peek()`: this function returns the next switchboard packet that would be received from a switchboard connection, but does not dequeue it.  In this model, we do not allow multiple outstanding responses, so `umi_mem` can only accept a UMI request involving a response if it does not have response pending for another request.  As a result, we have to peek at the incoming UMI request to see if it requires a response.  If it doesn't (e.g., `REQ_WRPOSTED`), we can accept the request with `SBRX.recv()` and implement it.  Otherwise, if a response is required, we can only accept the request if there isn't already a response pending.
