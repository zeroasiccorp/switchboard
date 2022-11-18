# General Makefile rules
#
# Copyright (C) 2022 Zero ASIC. 
#

CPPFLAGS += -I$(TOPDIR)/cpp
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

