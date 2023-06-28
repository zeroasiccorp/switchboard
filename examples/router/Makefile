EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

.PHONY: test
test: obj_dir/Vtestbench client
	./test.py

obj_dir/Vtestbench: \
	testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	$(EXDIR)/common/verilator/testbench.cc

	rm -rf obj_dir

	verilator --cc --exe -sv --build \
		--top-module testbench \
		-y $(SBDIR)/verilog/sim \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "-pthread" \
		$^

client: client.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

.PHONY: clean
clean:
	rm -rf obj_dir
	rm -f client
	rm -f queue-* *.q
