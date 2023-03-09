obj_dir/Vtestbench: timescale.sv \
	../../../verilog/sim/perf_meas_sim.sv \
	../../../verilog/sim/sb_rx_sim.sv \
	../../../verilog/sim/sb_tx_sim.sv \
	../../../verilog/sim/umi_rx_sim.sv \
	../../../verilog/sim/umi_tx_sim.sv \
	../../deps/umi/umi/rtl/umi_decode.v \
	../../deps/umi/umi/rtl/umi_pack.v \
	../../deps/umi/umi/rtl/umi_unpack.v \
	../verilog/axi_to_umi.v \
	../verilog/umi_to_axi.v \
	../verilog/picorv32.v \
	../../../deps/verilog-axi/rtl/arbiter.v \
	../../../deps/verilog-axi/rtl/priority_encoder.v \
	../../../deps/verilog-axi/rtl/axil_interconnect.v \
	../../../deps/verilog-axi/rtl/axil_dp_ram.v \
	../verilog/axil_interconnect_wrap_1x2.v \
	../verilog/dut.v \
	../verilog/testbench.sv \
	../../../dpi/switchboard_dpi.cc \
	testbench.cc
