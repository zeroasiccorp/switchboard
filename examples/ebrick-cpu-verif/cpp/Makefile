TOPDIR=../../..
include $(TOPDIR)/Rules.mk

OBJS += driver.o
TARGETS = driver

all: $(TARGETS)

-include $(OBJS:.o=.d)
CPPFLAGS += -MMD

SBDIR := $(shell switchboard --path)

driver: driver.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f $(OBJS)
	rm -f $(TARGETS)
