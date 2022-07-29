include files.d

obj_dir/Vtestbench:
	rm -rf obj_dir
	verilator \
		--cc \
		--exe \
		--build \
		-sv \
		--top testbench \
		-CFLAGS "-Wno-unknown-warning-option -I../../../../cpp" \
		-LDFLAGS "-lboost_system -lpthread" \
		../verilator/config.vlt \
		$^

.PHONY: clean
clean:
	rm -rf obj_dir
	rm -f *.vcd