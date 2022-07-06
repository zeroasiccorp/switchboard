.PHONY: verilator
verilator: obj_dir/Vtestbench_dpi
	./obj_dir/Vtestbench_dpi

obj_dir/Vtestbench_dpi:
	rm -rf obj_dir
	verilator --cc --exe --build \
		-sv \
		--top testbench_dpi \
		-CFLAGS "-Wno-unknown-warning-option" \
		-LDFLAGS "-lzmq" \
		testbench.cc \
		zmq_dpi.cc \
		../verilator/config.vlt \
		-f files.txt

.PHONY: clean
clean:
	rm -rf obj_dir