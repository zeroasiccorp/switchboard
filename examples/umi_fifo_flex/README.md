# umi_fifo_flex example

`umi_fifo_flex` is a module from the [UMI repository](https://github.com/zeroasiccorp/umi) that serves as an adapter between SUMI interfaces with different data widths.  For example, it can split up SUMI packets with wide data payloads to send them through a SUMI interface with a narrow data bus.  This example shows how to use switchboard to implement a loopback test through `umi_fifo_flex` to verify its operation.  It's conceptually similar to the [umi_fifo](../umi_fifo) example, but the required test logic is more complex, since it is not enough to directly compare the output stream of packets to the input stream, due to the fact that `umi_fifo_flex` may split and merge UMI packets.  Instead, we need to check that the output stream has the same meaning as the input stream.

Because this is a common pattern, we provide a library function for performing a loopback test, `umi_loopback()`.  The function accepts two main arguments: a `UmiTxRx` connection, and the number of SUMI packets to send into the DUT.  As you can see in [test.py](test.py), this allows for a loopback test to be implemented more concisely than in the [umi_fifo](../umi_fifo) example.

Assuming that `switchboard` is installed in your current Python environment, you can run the example with `./test.py`.  The output will look like this:
```text
100%|████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00, 29.11it/s]
```

The `3/3` output indicates that three packets were sent into the DUT.  You can change the number of packets sent with `-n NEW_VALUE`, e.g. `./test.py -n 100`.  We also suggest using the `--fast` flag to avoid rebuilding the simulator once it has already been built.

