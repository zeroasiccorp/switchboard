EXDIR := ../..
SBDIR := $(shell switchboard --path)

obj_dir/Vtestbench: timescale.sv \
	$(SBDIR)/verilog/sim/sb_rx_sim.sv \
	$(SBDIR)/verilog/sim/sb_tx_sim.sv \
	$(SBDIR)/verilog/sim/old_umi_rx_sim.sv \
	$(SBDIR)/verilog/sim/old_umi_tx_sim.sv \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_decode.v \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_pack.v \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_unpack.v \
	../verilog/umiram.sv \
	../verilog/testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	testbench.cc
