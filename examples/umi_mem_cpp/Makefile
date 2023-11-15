# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

LDLIBS := -pthread
CXXFLAGS := -O3 -Wall -Wextra -std=c++11

SWITCHBOARD_DIR ?= $(shell switchboard --path)

.PHONY: all
all: umi_mem

umi_mem: umi_mem.cc $(SWITCHBOARD_DIR)/cpp/switchboard.hpp
	g++ $(CXXFLAGS) -I. -I$(SWITCHBOARD_DIR)/cpp $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f umi_mem
	rm -f *.q
	rm -rf __pycache__
