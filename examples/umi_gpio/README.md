# umi_gpio example

This example shows how to set up bit-level interaction between Python and a running RTL simulation.  Assuming that `switchboard` is installed in your current Python environment, you can run the example with `./test.py`.  The output will look like this:

```text
Initial value: 0xcafed00d
gpio.o[7:0] = 22
gpio.o[15:8] = 77
Got gpio.i[7:0] = 34
Got gpio.i[15:8] = 43
Wrote gpio.o[:] = 0x9376b708291d2fa90c31e62a150a82ff
Read gpio.i[255:128] = 0x9376b708291d2fa90c31e62a150a82ff
Read gpio.i[383:256] = 0x6c8948f7d6e2d056f3ce19d5eaf57d00
PASS!
```

Here's what the interaction looks like from the Python perspective (with reference to [test.py](test.py)):
1. Create a `UmiGpio` object from a `UmiTxRx` object using the `.gpio(...)` method.  It is possible to run multiple GPIO interfaces from a single `UmiTxRx` object if they are given different `dstaddr` values.
2. Let's say that the `UmiGpio` object is called `gpio`.  You can write bits using statements like `gpio.o[msb:lsb] = ...` or `gpio.o[idx] = ...`.  Note that Verilog bit-select syntax is used, where the MSB is before the colon and the LSB is after, and both are included in the bit selection.  (This is different than how Python slice notation usually works.)
3. Reading from GPIO interface works in a similar fashion: `... = gpio.i[msb:lsb]` or `... = gpio.i[idx]`.

Under the hood, these reads and writes are implemented using UMI transactions.  For example, if you write `gpio.o[7:0] = 42`, a UMI write request is sent to a switchboard connection, indicating that bits 7-0 should be written to the value `42`.

From the RTL simulation perspective, bit-level interaction happens through instances of the `umi_gpio` module, which is provided by the switchboard repository.  Connect bit-level signals to be read from Python to the `gpio_in` port of `umi_gpio`, and similarly connect bit-level signals to be written from Python to the `gpio_out` port of `umi_gpio`.  The width of the `gpio_in` port is set by the `IWIDTH` parameter and the width of the `gpio_out` port is set by the `OWIDTH` parameter; the values set for those parameters in RTL should match the values provided to the `UmiTxRx.gpio(...)` method when constructing a `UmiGpio` object.
