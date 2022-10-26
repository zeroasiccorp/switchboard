obj_dir/Vtestbench: timescale.sv \
	../../../verilog/sim/sb_rx_sim.sv \
	../../../verilog/sim/sb_tx_sim.sv \
	../verilog/testbench.sv \
	../../../dpi/switchboard_dpi.cc \
	testbench.cc
	../../../cpp/switchboard.hpp \
