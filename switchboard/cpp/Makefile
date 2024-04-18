# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

TARGETS = umidriver old_umidriver router old2new

all: $(TARGETS)

%: %.cc switchboard.hpp
	g++ -std=c++11 -I. $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f $(TARGETS)
