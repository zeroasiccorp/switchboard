# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

-include .config.mk

SYSTEMC ?= /usr
SYSTEMC_INCLUDE ?=$(SYSTEMC)/include/
SYSTEMC_LIBDIR ?= $(SYSTEMC)/lib-linux64

VERILATOR ?= verilator
VERILATOR_ROOT?=$(shell $(VERILATOR) --getenv VERILATOR_ROOT 2>/dev/null || echo -n /usr/share/verilator)

EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

VOBJ_DIR=obj_dir

VFLAGS += --exe
VFLAGS += --assert
VFLAGS += -Wno-TIMESCALEMOD
VFLAGS += --trace
VFLAGS += --sc --pins-bv 2
VFLAGS += -Mdir $(VOBJ_DIR)
VFLAGS += --MMD

VERILATED_OBJS_COMMON += verilated_vcd_c.o
VERILATED_OBJS_COMMON += verilated_vcd_sc.o
CXXFLAGS += -DVM_TRACE=1

VENV=SYSTEMC_INCLUDE=$(SYSTEMC_INCLUDE) SYSTEMC_LIBDIR=$(SYSTEMC_LIBDIR)

CPPFLAGS += -I. -I$(VERILATOR_ROOT)/include/
CPPFLAGS += -I $(EXDIR)/deps/libsystemctlm-soc/ -I $(EXDIR)/deps/libsystemctlm-soc/tests/
CPPFLAGS += -I $(SBDIR)/cpp/
CPPFLAGS += -I $(SYSTEMC_INCLUDE)
CPPFLAGS += -DVM_TRACE=1
OPT_FAST ?= -O2 -fno-stack-protector -fno-var-tracking-assignments
OPT_SLOW ?= -O1 -fstrict-aliasing -fno-var-tracking-assignments
export OPT_FAST
export OPT_SLOW

CXXFLAGS += -Wall -O3 -g -faligned-new
LDFLAGS  += -L $(SYSTEMC_LIBDIR)

SC_FILES_COMMON += $(EXDIR)/deps/libsystemctlm-soc/trace/trace.cc

# To make the filenames match the top module
# (and avoid additional args to verilator we use underscores instead
# of hyphens.

RTL_DIR = $(SBDIR)/verilog/fpga
VFLAGS += -I$(RTL_DIR)/include/
VFLAGS += --top-module loopback
SC_FILES_loopback += loopback_tb.cc
SV_FILES_loopback += $(RTL_DIR)/axi_reader.sv
SV_FILES_loopback += $(RTL_DIR)/axi_writer.sv
SV_FILES_loopback += $(RTL_DIR)/config_registers.sv
SV_FILES_loopback += $(RTL_DIR)/sb_rx_fpga.sv
SV_FILES_loopback += $(RTL_DIR)/sb_tx_fpga.sv
SV_FILES_loopback += $(RTL_DIR)/memory_fault.sv
SV_FILES_loopback += $(RTL_DIR)/sb_fpga_queues.sv
SV_FILES_loopback += ./loopback.sv
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/arbiter.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_crossbar.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_crossbar_addr.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_crossbar_rd.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_crossbar_wr.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_register.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_register_rd.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axi_register_wr.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axil_reg_if.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axil_reg_if_rd.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axil_reg_if_wr.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axil_register.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axil_register_rd.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/axil_register_wr.v
SV_FILES_loopback += $(SBDIR)/deps/verilog-axi/rtl/priority_encoder.v

VLT_CONFIG_FILE = ./config.vlt
ALL += $(VOBJ_DIR)/Vloopback.build

all: $(ALL)

$(VOBJ_DIR)/V%.build:
	$(VENV) $(VERILATOR) $(VFLAGS) $(VLT_CONFIG_FILE) $(SV_FILES_$(*)) $(SC_FILES_COMMON) $(SC_FILES_$(*))
	$(MAKE) -C $(VOBJ_DIR) -f V$(*).mk CPPFLAGS="$(CPPFLAGS)" CXXFLAGS="$(CXXFLAGS)" V$(*)

clean distclean:
	$(RM) -fr $(VOBJ_DIR)
	$(RM) -f queue-*

.PHONY: test
test: $(VOBJ_DIR)/Vloopback.build
	$(VOBJ_DIR)/Vloopback
