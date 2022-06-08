all: hex simulator

.PHONY: run simulator hex qemu spike clean

# run Verilator simulator
run:
	fusesoc --cores-root=. run --run ::testbench \
	--run_options "+firmware=`realpath firmware/firmware.hex`"

# build Verilator simulator
simulator:
	fusesoc --cores-root=. run --setup --build ::testbench

# compile HEX
hex:
	make -C firmware

# run QEMU simulation (compiling binary file if needed)
qemu:
	make -C firmware qemu

# run Spike simulation (compiling binary file if needed)
spike:
	make -C firmware spike

# clean build outputs
clean:
	rm -rf build
	make -C firmware clean
