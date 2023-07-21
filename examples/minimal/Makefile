EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

.PHONY: verilator
verilator: obj_dir/Vtestbench client
	./test.py verilator

.PHONY: icarus
icarus: client switchboard_vpi.vpi
	./test.py icarus

client: client.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

obj_dir/Vtestbench: \
	testbench.sv \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	$(EXDIR)/common/verilator/testbench.cc

	rm -rf obj_dir

	verilator --cc --exe -sv --trace-fst --build \
		--top-module testbench \
		-y $(SBDIR)/verilog/sim \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "-pthread" \
		$^

switchboard_vpi.o: $(SBDIR)/vpi/switchboard_vpi.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -c -o $@ `iverilog-vpi --cflags` -std=c++11 -pthread -I$(SBDIR)/cpp $<

switchboard_vpi.vpi: switchboard_vpi.o
	g++ -o $@ `iverilog-vpi --ldflags` $< -pthread `iverilog-vpi --ldlibs`

.PHONY: clean
clean:
	rm -f client
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -f *.o *.vpi *.vvp
	rm -rf obj_dir
