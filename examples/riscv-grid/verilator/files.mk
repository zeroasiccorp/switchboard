EXDIR := ../..
SBDIR := $(shell switchboard --path)

obj_dir/Vtestbench: timescale.sv \
	$(SBDIR)/verilog/sim/perf_meas_sim.sv \
	$(SBDIR)/verilog/sim/sb_rx_sim.sv \
	$(SBDIR)/verilog/sim/sb_tx_sim.sv \
	$(SBDIR)/verilog/sim/old_umi_rx_sim.sv \
	$(SBDIR)/verilog/sim/old_umi_tx_sim.sv \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_decode.v \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_pack.v \
	$(EXDIR)/deps/old-umi/umi/rtl/umi_unpack.v \
	../verilog/axi_to_umi.v \
	../verilog/umi_to_axi.v \
	../verilog/picorv32.v \
	$(SBDIR)/deps/verilog-axi/rtl/arbiter.v \
	$(SBDIR)/deps/verilog-axi/rtl/priority_encoder.v \
	$(SBDIR)/deps/verilog-axi/rtl/axil_interconnect.v \
	$(SBDIR)/deps/verilog-axi/rtl/axil_dp_ram.v \
	../verilog/axil_interconnect_wrap_1x2.v \
	../verilog/dut.v \
	../verilog/testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	testbench.cc
