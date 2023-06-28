EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

.PHONY: test
test: obj_dir/Vtestbench
	./test.py

obj_dir/Vtestbench: \
	testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	$(EXDIR)/common/verilator/testbench.cc

	rm -rf obj_dir

	verilator --cc --exe -sv --trace-fst --build \
		--top-module testbench \
		-y $(SBDIR)/verilog/sim \
		-y $(EXDIR)/deps/umi/umi/rtl \
		-I$(EXDIR)/deps/umi/umi/rtl \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "-pthread" \
		$(EXDIR)/common/verilator/config.vlt $^

.PHONY: clean
clean:
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir
