# minimal example

This example shows how to interact with RTL code from C++ using switchboard, with build and run automation provided by Python.  The C++ code sends a switchboard packet containing a number to RTL, which increments the number and sends it back to the C++ code in a new switchboard packet.  To run the example, type `make`.  You'll see a Verilator build, followed by output like this:

```text
TX packet: dest: beefcafe, last: 1, data: {00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 0a, 0b, 0c, 0d, 0e, 0f, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 1a, 1b, 1c, 1d, 1e, 1f}
RX packet: dest: beefcafe, last: 1, data: {01, 02, 03, 04, 05, 06, 07, 08, 09, 0a, 0b, 0c, 0d, 0e, 0f, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 1a, 1b, 1c, 1d, 1e, 1f, 20}
PASS!
```

Looking at the [client.cc](client.cc) C++ code, the outbound switchboard connection is created as an instance of `SBTX`, and the outbound packet is sent with `SBTX.send_blocking()`.  The packet itself is an `sb_packet` struct.  In the [testbench.sv](testbench.sv) RTL code, this packet is received by an instance of the `queue_to_sb_sim` module, created with the `QUEUE_TO_SB_SIM` macro from `switchboard.vh`.  The data payload is incremented and assigned to a new switchboard packet, which is transmitted back to C++ code with an instance of the `sb_to_queue_sim` module, created with the `SB_TO_QUEUE_SIM` macro.  The C++ code receives that packet via the `SBRX.recv_blocking()` method.

The Python code [test.py](test.py) isn't directly involved in this interaction, but it does act as the orchestrator, first building the RTL simulation, then running it alongside the binary built from [client.cc](client.cc).  Build automation for this example supports both Verilator and Icarus Verilog; changing between the two is just a matter of setting the `tool` argument for `SbDut`.  If you want to run this example with Icarus Verilog, type `make icarus` instead of `make`.
