TOPDIR=../../..
include $(TOPDIR)/Rules.mk

.DEFAULT_GOAL := all

include files.d

.PHONY: all
all: switchboard_vpi.vpi testbench.vvp

%.o: ../../../vpi/%.cc ../../../cpp/switchboard.hpp
	g++ -c -o $@ `iverilog-vpi --cflags` -std=c++11 $(CXXFLAGS) -I../../../cpp $<

%.vpi: %.o
	g++ -o $@ `iverilog-vpi --ldflags` $< $(LDFLAGS) $(LDLIBS) `iverilog-vpi --ldlibs`

testbench.vvp:
	iverilog -g2012 -s testbench -o testbench.vvp $^

.PHONY: clean
clean:
	rm -f *.vcd *.vvp *.vpi *.o
	rm -rf *.dSYM
