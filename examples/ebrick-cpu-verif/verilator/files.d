obj_dir/Vtestbench: timescale.sv \
	../dut-rtl/umi_decode.v \
	../dut-rtl/umi_pack.v \
	../dut-rtl/umi_unpack.v \
	../dut-rtl/picorv32.v \
	../dut-rtl/axi_umi_bridge.v \
	../dut-rtl/ebrick_core.v \
	../../../verilog/sim/umi_rx_sim.sv \
	../../../verilog/sim/umi_tx_sim.sv \
	../verif-rtl/umi_gpio.v \
	../verif-rtl/testbench.v \
	../../../dpi/switchboard_dpi.cc \
	testbench.cc
