# Interposer Verification

[![Actions Status](https://github.com/zeroasiccorp/interposer-verif/actions/workflows/regression.yml/badge.svg)](https://github.com/zeroasiccorp/interposer-verif/actions)

Repository containing infrastructure and tests for the interposer design; eventually tests may be moved to a separate repository.  Currently contains code to run a "Hello World" program on a PicoRV32 processor with Verilator, with simple output checks performed in GitHub Actions.

## Installation

Clone the repository:

```shell
git clone https://github.com/zeroasiccorp/interposer-verif.git
```

Then install the prerequisites as described below for Linux and macOS.  You may want to consider `pip`-installing in a `conda` environment, if you think that you will need to have multiple versions of `fusesoc` for different projects, or if you just want to avoid cluttering the base environment.

### Linux

```shell
pip3 install fusesoc
```

```shell
sudo apt-get install verilator gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
```

### macOS

```shell
pip3 install fusesoc
```

```shell
brew tap riscv/riscv
```

```shell
brew install riscv-tools verilator
```

## Running the code

* ``make simulator``: Build a simulator binary with Verilator
* ``make hex``: Build a binary to use in the simulator.
* ``make run``: Run the simulator using the binary that was built.

## Related

The starting point for this work was PicoRV32 and its simulation flow (https://github.com/YosysHQ/picorv32).  That code was reorganized towards our goal of having a separate verification repository, although the PicoRV32 implementation still resides here since interposer RTL is not yet available.  While PicoRV32 could have been pulled in via FuseSoC, it turns out that it needed to be slightly edited to support the default Verilator versions installed on Ubuntu (via `apt`) and macOS (via `brew`).  So for now, the PicoRV32 source code is in this repository, and it will be removed once interposer RTL is available.

Since the starting point for this RTL top-level verification flow will be ELF files from higher-level software tools, this repository contains only minimal infrastructure to generate basic ELF files, such as the "Hello World" program in `firmware`.  This program was adapted from https://github.com/noteed/riscv-hello-asm.

In the future, it may be worth exploring the verification infrastructure used for Ibex (https://github.com/lowRISC/ibex).  The infrastructure is modular, allowing for various devices to be added to different places in the address space, and has various capabilities for software interaction with simulated RTL through DPI routines.

On a similar note, it would be worth using features from the Ariane/CVA6 verification infrastructure in the future (https://github.com/openhwgroup/core-v-verif).  I did manage to get verification flows running for Ibex and CV32E40P (small processor related to CVA6), but decided to use PicoRV32 as the starting point, since it has a simple structure that lends itself well to customization (as well as really understanding the details of how it works, which will be useful for debugging).
