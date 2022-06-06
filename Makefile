all: hex simulator

.PHONY: run simulator hex clean

# run Verilator simulator
run:
	fusesoc --cores-root=. run --run ::testbench \
	--run_options +firmware=`realpath firmware/firmware.hex`

# build Verilator simulator
simulator:
	fusesoc --cores-root=. run --setup --build ::testbench

# compile HEX
hex:
	make -C firmware

# clean build outputs
clean:
	rm -rf build
	make -C firmware clean
