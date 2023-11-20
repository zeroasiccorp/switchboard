# General Makefile rules

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

SBDIR := $(shell switchboard --path)
CPPFLAGS += -I$(SBDIR)/cpp
CXXFLAGS += -Wall -O3 -g
CFLAGS += -Wall -O3 -g

CXXFLAGS += -pthread
CFLAGS += -pthread
LDFLAGS += -pthread

%.o: %.cc
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< -c -o $@ $(LDFLAGS) $(LDLIBS)

%.out: %.cc
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

%.out: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

