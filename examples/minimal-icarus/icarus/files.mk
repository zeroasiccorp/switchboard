SBDIR := $(shell switchboard --path)

testbench.vvp: $(SBDIR)/verilog/sim/sb_rx_sim.sv \
	$(SBDIR)/verilog/sim/sb_tx_sim.sv \
	../verilog/testbench.sv
