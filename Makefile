# Modified from ibex

# name of the program to run
program-name := hello_test

# compiled Verilator simulator
simulator-binary := build/lowrisc_ibex_ibex_simple_system_0/sim-verilator/Vibex_simple_system

# compiled ELF
program-elf := sw/$(program-name)/$(program-name).elf

# run Verilator simulator
.PHONY: run
run:
	$(simulator-binary) --meminit=ram,$(program-elf)

# build Verilator simulator
.PHONY: simulator
simulator:
	fusesoc --cores-root=. run --target=sim --setup --build lowrisc:ibex:ibex_simple_system

# compile ELF
.PHONY: elf
elf:
	make -C sw/$(program-name)
