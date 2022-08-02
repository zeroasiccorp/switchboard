obj_dir/Vtestbench: timescale.sv \
	../../../verilog/sim/perf_meas_sim.sv \
	../../../verilog/sim/umi_rx_sim.sv \
	../../../verilog/sim/umi_tx_sim.sv \
	../verilog/umi/umi/rtl/umi_decode.v \
	../verilog/umi/umi/rtl/umi_pack.v \
	../verilog/umi/umi/rtl/umi_unpack.v \
	../verilog/axi_to_umi.v \
	../verilog/umi_to_axi.v \
	../verilog/picorv32.v \
	../verilog/verilog-axi/rtl/arbiter.v \
	../verilog/verilog-axi/rtl/priority_encoder.v \
	../verilog/verilog-axi/rtl/axil_interconnect.v \
	../verilog/verilog-axi/rtl/axil_dp_ram.v \
	../verilog/axil_interconnect_wrap_1x2.v \
	../verilog/dut.v \
	../verilog/testbench.sv \
	../../../dpi/umiverse_dpi.cc \
	testbench.cc