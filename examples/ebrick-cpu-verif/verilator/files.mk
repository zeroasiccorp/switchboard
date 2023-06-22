EXDIR := ../..
SBDIR := $(shell switchboard --path)

obj_dir/Vtestbench: timescale.sv \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_decode.v \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_pack.v \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_unpack.v \
	../dut-rtl/picorv32.v \
	../dut-rtl/axi_umi_bridge.v \
	../dut-rtl/ebrick_core.v \
	$(SBDIR)/verilog/sim/sb_rx_sim.sv \
	$(SBDIR)/verilog/sim/sb_tx_sim.sv \
	$(SBDIR)/verilog/sim/old_umi_rx_sim.sv \
	$(SBDIR)/verilog/sim/old_umi_tx_sim.sv \
	../verif-rtl/umi_gpio.v \
	../verif-rtl/testbench.v \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	testbench.cc
