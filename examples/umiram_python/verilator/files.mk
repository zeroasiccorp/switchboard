obj_dir/Vtestbench: timescale.sv \
	../../../verilog/sim/sb_rx_sim.sv \
	../../../verilog/sim/sb_tx_sim.sv \
	../../../verilog/sim/umi_rx_sim.sv \
	../../../verilog/sim/umi_tx_sim.sv \
	../../deps/umi/umi/rtl/umi_decode.v \
	../../deps/umi/umi/rtl/umi_pack.v \
	../../deps/umi/umi/rtl/umi_unpack.v \
	../verilog/umiram.sv \
	../verilog/testbench.sv \
	../../../dpi/switchboard_dpi.cc \
	testbench.cc
