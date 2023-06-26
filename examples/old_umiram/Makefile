EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

.PHONY: python
python: obj_dir/Vtestbench
	./test.py --mode python

.PHONY: cpp
cpp: obj_dir/Vtestbench client
	./test.py --mode cpp

obj_dir/Vtestbench: \
	testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	$(EXDIR)/common/verilator/testbench.cc

	rm -rf obj_dir

	verilator --cc --exe -sv --trace --build \
		--top-module testbench \
		-y $(EXDIR)/common/old-verilog \
		-y $(SBDIR)/verilog/sim \
		-y $(EXDIR)/deps/old-umi/umi/rtl \
		-I$(EXDIR)/deps/old-umi/umi/rtl \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "$(LDFLAGS)" \
		$(EXDIR)/common/verilator/config.vlt \
		$^

client: client.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

.PHONY: clean
clean:
	rm -f client
	rm -rf obj_dir
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
