# run Verilator simulator
.PHONY: run
run:
	fusesoc --cores-root=. run --run ::testbench \
	--run_options +firmware=`realpath firmware/firmware.hex`

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