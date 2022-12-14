# FPGA loopback

Basic loopback design to demonstrate FPGA Switchboard queues.

## Simulation

Install the needed prerequisites:

### Linux

```shell
sudo apt-get install verilator
```

### macOS

```shell
brew install verilator
```

### Build

```shell
make
```

### Run

```shell
./obj_dir/Vloopback
```

Add the `+trace` option to dump waveforms.
