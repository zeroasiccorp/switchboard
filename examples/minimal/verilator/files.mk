SBDIR := $(shell switchboard --path)

obj_dir/Vtestbench: timescale.sv \
	$(SBDIR)/verilog/sim/sb_rx_sim.sv \
	$(SBDIR)/verilog/sim/sb_tx_sim.sv \
	../verilog/testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	testbench.cc
