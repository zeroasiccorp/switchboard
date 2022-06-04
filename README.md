# Interposer Verification

[![Actions Status](https://github.com/zeroasiccorp/interposer-verif/actions/workflows/regression.yml/badge.svg)](https://github.com/zeroasiccorp/interposer-verif/actions)

Repository containing infrastructure and tests for the interposer design; eventually tests may be moved to a separate repository.  Currently contains code to run a "Hello World" program on a PicoRV32 processor with Verilator, with simple output checks performed in GitHub Actions.

## Related

The starting point for this work was PicoRV32 and its simulation flow (https://github.com/YosysHQ/picorv32).  That code was reorganized towards our goal of having a separate verification repository, although the PicoRV32 implementation still resides here since interposer RTL is not yet available.  While PicoRV32 could have been pulled in via FuseSoC, it turns out that it needed to be slightly edited to support the default Verilator versions installed on Ubuntu (via `apt`) and macOS (via `brew`).  So for now, the PicoRV32 source code is in this repository, and it will be removed once interposer RTL is available.

Since the starting point for this RTL top-level verification flow will be ELF files from higher-level software tools, this repository contains only minimal infrastructure to generate basic ELF files, such as the "Hello World" program in `firmware`.  This program was adapted from https://github.com/noteed/riscv-hello-asm.

In the future, it may be worth exploring the verification infrastructure used for Ibex (https://github.com/lowRISC/ibex).  The infrastructure is modular, allowing for various devices to be added to different places in the address space, and has various capabilities for software interaction with simulated RTL through DPI routines.

On a similar note, it would be worth using features from the Ariane/CVA6 verification infrastructure in the future (https://github.com/openhwgroup/core-v-verif).  I did manage to get verification flows running for Ibex and CV32E40P (small processor related to CVA6), but decided to use PicoRV32 as the starting point, since it has a simple structure that lends itself well to customization (as well as really understanding the details of how it works, which will be useful for debugging).
