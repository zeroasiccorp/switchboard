# Makefile

# simulator options are icarus, verilator, vcs
SIM ?= icarus

TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES :=
ifeq ($(SIM), verilator)
	VERILOG_SOURCES := $(VERILOG_SOURCES) ../verilator/config.vlt
endif
VERILOG_SOURCES := $(VERILOG_SOURCES) \
	../verilog/umi/umi/rtl/umi_decode.v \
	../verilog/umi/umi/rtl/umi_pack.v \
	../verilog/umi/umi/rtl/umi_unpack.v \
	../verilog/axi_to_umi.v \
	../verilog/umi_to_axi.v \
	../../rtl/picorv32.v \
	../verilog/verilog-axi/rtl/arbiter.v \
	../verilog/verilog-axi/rtl/priority_encoder.v \
	../verilog/verilog-axi/rtl/axil_interconnect.v \
	../verilog/verilog-axi/rtl/axil_dp_ram.v \
	../verilog/axil_interconnect_wrap_1x2.v \
	../verilog/zverif_top.v
# use VHDL_SOURCES for VHDL files

# define environment variables.  for some reason, using the same name
# as the environment variable to be exported does not work
ifeq ($(SIM), verilator)
	CPR := 10
	CPM := 6000
else ifeq ($(SIM), icarus)
	CPR := 10
	CPM := 5000
else ifeq ($(SIM), vcs)
	CPR := 10
	CPM := 6000
endif
all: export CYCLES_PER_RECV=$(CPR)
all: export CYCLES_PER_MEAS=$(CPM)
all: export RX_PORT=5555
all: export TX_PORT=5556

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = zverif_top

# MODULE is the basename of the Python test file
MODULE = zmq_server

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim