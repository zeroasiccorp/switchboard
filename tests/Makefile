# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

TOPDIR=..
include $(TOPDIR)/Rules.mk

TESTS := hello bandwidth latency

ifeq ($(TCP),1)
	OPTIONS += --tcp
else
	TESTS += torture
endif

test: $(TESTS)

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
	./test.py --test hello $(OPTIONS)

.PHONY: bandwidth
bandwidth: bandwidth.out
	./test.py --test bandwidth $(OPTIONS)

.PHONY: latency
latency: latency.out
	./test.py --test latency $(OPTIONS)

.PHONY: torture
torture: torture.out
	./$<

.PHONY: clean
clean:
	rm -f $(TARGETS)
	rm -f $(TARGETS:.out=.d)
	rm -f queue-*
	rm -rf *.out.dSYM
