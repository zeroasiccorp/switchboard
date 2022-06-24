# Interposer Verification

[![Actions Status](https://github.com/zeroasiccorp/interposer-verif/actions/workflows/regression.yml/badge.svg)](https://github.com/zeroasiccorp/interposer-verif/actions)

Repository containing infrastructure and tests as a mockup for the verification of the interposer design.  Currently contains code to run a "Hello World" program on a PicoRV32 processor with both Verilator and Spike, in addition to running a standard suite of tests checking compliance with the RISC-V ISA.  These simulation and emulation tests are used in GitHub Actions to produce a pass/fail result for pull request regression testing.

## Installation

Clone the repository and change to its directory:

```shell
git clone https://github.com/zeroasiccorp/interposer-verif.git
```

```shell
cd interposer-verif
```

Then install the included `zverif` package as described below.  You may want to consider `pip`-installing in a `conda` environment, or other virtual environment.

```shell
pip3 install -e .
```

Finally, install tools for RISC-V and RTL simulation using the commands below.

### Linux

```shell
sudo apt-get install verilator gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
```

### macOS

```shell
brew tap riscv/riscv
```

```shell
brew install riscv-tools verilator
```

## Running the code

Verification tasks are run via the script `interposer/verif/verif.py`.  For example, to run a "hello world" program (`interposer/verif/sw/hello/hello.c`) using a Verilator simulation, run:

```shell
cd interposer/verif
```

```shell
./verif.py verilator:hello
```

Or similarly, to run the Spike emulator on a simple addition test from the RISC-V test suite, type:

```shell
./verif.py spike:add
```

Under the hood, these commands are running intermediate tasks as needed, making use of a Python library called `doit`.  For example, running a Verilator simulation requires RTL to be converted to C, and then compiled with a top-level testbench.  It also requires the RISC-V compilation chain to be run to produce a `*.hex` file readable in the Verilator simulation.  The result is a directed graph of dependencies between tasks, which is managed by `doit` to avoid doing unecessary work.

Build results, such as ELF files or a Verilator simulation binary, are placed in a `build` directory, and the state of `doit` is maintained in a file called `.doit.db.db`.  If either is deleted or corrupted, `doit` will figure out what needs to be done to rebuild the next time a task is run.

To see available tasks, type `./verif.py list` for a short summary, or `./verif.py list --all` to see all avilable tasks.  There are currently tasks for generating various kinds of binaries (`*.elf`, `*.bin`, `*.hex`) for compiled RISC-V programs, in addition to Spike and Verilator simulation.

All of these tasks allow the application name to be specified with a colon, as shown earlier (e.g., `verilator:hello`).  Running one of these tasks without a colon means that all applications should be tested.  For example, typing `./verif.py verilator` means "run a Verilator simulation for each application".

`doit` tasks are represented by a graph, and it can be interesting to visualize that graph.  To do that, there is a plugin called `doit-graph` (`pip install doit-graph`).  For example, if you install the plugin and then run:

```shell
./verif.py graph --show-subtasks --reverse -o tasks.dot verilator:hello && dot -Tpng tasks.dot -o tasks.png
```

you will see a graph representing actions that need to be taken to run a Verilator simulation: first an `*.elf` file is build, which is converted to `*.bin` and then `*.hex`.  In addition, the Verilator simulation binary is built.  `doit` has flags `-n` and `-P` to control how independent branches such as these can be run in parallel, although I haven't experimented with that feature yet.

A few other notes:
* `./verif.py` presents exactly the same command-line interface as `doit`, which is documented here: https://pydoit.org/contents.html.
* The `spike` task depends on a group of tasks called `spike_plugin`, which builds memory-mapped plugins for the Spike emulator.  Currently, there are just two: `uart_plugin`, which receives characters for printing, and `exit_plugin`, which exits the Spike emulator.  The RTL model has an equivalent memory map, so the exact same binary will run in Verilator and Spike.
* Multiple tasks can be specified on the command-line, e.g. `./verif.py verilator:hello spike:hello`.  Even though these both depend on `hello.elf`, it is only built once (or possibly not built at all, if it exists and is up-to-date in terms of its dependencies).

## Related

The starting point for this work was PicoRV32 and its simulation flow (https://github.com/YosysHQ/picorv32).  It's included directly in this repository, instead of using a submodule, because it turned out that the processor implementation needed to be slightly edited to support the default Verilator version installed on Ubuntu (via `apt`) and macOS (via `brew`).

In the future, it may be worth exploring the verification infrastructure used for Ibex (https://github.com/lowRISC/ibex).  The infrastructure is modular, allowing for various devices to be added to different places in the address space, and has various capabilities for software interaction with simulated RTL through DPI routines.

On a similar note, it could be worth using features from the Ariane/CVA6 verification infrastructure in the future (https://github.com/openhwgroup/core-v-verif).  I did manage to get verification flows running for Ibex and CV32E40P (small processor related to CVA6), but decided to use PicoRV32 as the starting point, since it has a simple structure that lends itself well to customization.
