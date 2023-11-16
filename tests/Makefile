# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

TOPDIR=..
include $(TOPDIR)/Rules.mk

MODE ?= queue

test: torture

TARGETS += hello.out
TARGETS += bandwidth.out
TARGETS += latency.out
TARGETS += torture.out

all: $(TARGETS)

-include $(OBJS:.o=.d)
-include $(TARGETS:.out=.d)
CPPFLAGS += -MMD

.PHONY: hello
hello: hello.out
	./test.py --test hello

.PHONY: bandwidth
bandwidth: bandwidth.out
	./test.py --test bandwidth

.PHONY: latency
latency: latency.out
	./test.py --test latency

.PHONY: torture
torture: torture.out
	./$<

.PHONY: clean
clean:
	rm -f $(TARGETS)
	rm -f $(TARGETS:.out=.d)
	rm -f queue-*
	rm -rf *.out.dSYM
