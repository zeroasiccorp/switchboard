# Modified from ibex

# name of the program to run
program-name := hello_test

# compiled Verilator simulator
simulator-binary := build/zeroasic_interposer_verif_picorv32_simple_system_0/default-verilator/Vpicorv32_simple_system

# run Verilator simulator
.PHONY: run
run:
	$(simulator-binary)

# build Verilator simulator
.PHONY: simulator
simulator:
	fusesoc --cores-root=. run --setup --build ::testbench

# compile HEX
.PHONY: hex
hex:
	make -C firmware

# clean build outputs
.PHONY: clean
clean:
	rm -rf build
	make -C firmware clean