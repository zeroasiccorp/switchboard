# axil_reset

Regression test for [issue #275](https://github.com/zeroasiccorp/switchboard/issues/275).

The DUT (`axil_reset_check.sv`) models a simple AXI-Lite register interface whose
handshake logic ignores reset, so all three `ready` signals are high from time
zero -- including while the design is still in reset. It counts every transaction
accepted while `rst` was asserted and returns that count for any read.

A transactor that drives transactions without regard to reset gets them accepted
before the design is ready. In a real DUT those transactions are silently dropped
and the simulation hangs waiting for a response; here the count is non-zero and
the test fails instead.

Run with:

```console
make verilator
make icarus
```
