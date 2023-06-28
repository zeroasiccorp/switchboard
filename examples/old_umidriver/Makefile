EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

.PHONY: test
test: $(SBDIR)/cpp/old_umidriver obj_dir/Vtestbench
	$(SBDIR)/cpp/old_umidriver --sim obj_dir/Vtestbench --txfile in.memh --rxfile expect.memh

$(SBDIR)/cpp/old_umidriver:
	make -C $(SBDIR)/cpp old_umidriver

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

.PHONY: clean
clean:
	rm -rf obj_dir
	rm -f $(SBDIR)/cpp/old_umidriver
	rm -f queue-* *.q
