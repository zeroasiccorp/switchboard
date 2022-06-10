all: firmware simulator

.PHONY: run firmware simulator qemu spike clean

# run Verilator simulator
run: firmware simulator
	fusesoc --cores-root=. run --run ::testbench \
	--run_options "+firmware=`realpath firmware/firmware.hex`"

# build Verilator simulator
simulator:
	fusesoc --cores-root=. run --setup --build ::testbench

# compile HEX
firmware:
	make -C firmware

# run QEMU simulation (compiling binary file if needed)
qemu: firmware
	make -C qemu

# run Spike simulation (compiling binary file if needed)
spike:
	make -C firmware spike

# clean build outputs
clean:
	rm -rf build
	make -C firmware clean
