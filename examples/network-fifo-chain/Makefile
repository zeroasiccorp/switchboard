# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

.PHONY: verilator
verilator:
	./test.py --tool verilator --start-delay 5 --max-rate 1e3

.PHONY: verilator-single-netlist
verilator-single-netlist:
	./test.py --tool verilator --single-netlist

.PHONY: icarus
icarus:
	./test.py --tool icarus --start-delay 2 --max-rate 1e3 --fifos 125

.PHONY: icarus-single-netlist
icarus-single-netlist:
	./test.py --tool icarus --single-netlist

.PHONY: clean
clean:
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
	rm -f *.o *.vpi
