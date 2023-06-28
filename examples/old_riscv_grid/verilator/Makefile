EXDIR := $(abspath ../..)
SBDIR := $(shell switchboard --path)

LDFLAGS := -pthread
ifeq ($(UNAME_S),Darwin)
	LDFLAGS := $(LDFLAGS) -undefined dynamic_lookup
endif

obj_dir/Vtestbench: \
	$(EXDIR)/common/verilog/picorv32.v \
	../verilog/axil_interconnect_wrap_1x2.v \
	../verilog/dut.v \
	../verilog/testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	$(EXDIR)/common/verilator/testbench.cc
	rm -rf obj_dir
	verilator --cc --exe -sv \
		--top-module testbench --timescale 1ns/1ps \
		-y $(SBDIR)/verilog/sim \
		-y $(EXDIR)/common/old-verilog \
		-y $(SBDIR)/deps/verilog-axi/rtl \
		-y $(EXDIR)/deps/old-umi/umi/rtl \
		-I$(EXDIR)/deps/old-umi/umi/rtl \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "$(LDFLAGS)" $(EXDIR)/common/verilator/config.vlt \
		$^
	make -C obj_dir -f Vtestbench.mk Vtestbench

.PHONY: clean
clean:
	rm -rf obj_dir
	rm -f *.vcd
