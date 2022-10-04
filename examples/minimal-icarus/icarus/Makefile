.DEFAULT_GOAL := all

include files.d

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	CPP_LIBS := -lboost_system -lpthread
else
	CPP_LIBS := -lboost_system -pthread -lrt
endif

.PHONY: all
all: switchboard_vpi.vpi testbench.vvp

%.o: ../../../vpi/%.cc ../../../cpp/switchboard.hpp
	g++ -c -o $@ `iverilog-vpi --cflags` -std=c++11 -I../../../cpp $<

%.vpi: %.o
	g++ -o $@ `iverilog-vpi --ldflags` $< $(CPP_LIBS) `iverilog-vpi --ldlibs`

testbench.vvp:
	iverilog -g2012 -s testbench -o testbench.vvp $^

.PHONY: clean
clean:
	rm -f *.vcd *.vvp *.vpi *.o
	rm -rf *.dSYM
