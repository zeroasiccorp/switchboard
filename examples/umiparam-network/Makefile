# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

.PHONY: verilator
verilator:
	./test.py --tool verilator --max-rate 1e3 --fast

.PHONY: verilator-single-netlist
verilator-single-netlist:
	./test.py --tool verilator --single-netlist --fast

.PHONY: verilator-supernet
verilator-supernet:
	./test.py --tool verilator --supernet --max-rate 1e3 --fast

.PHONY: icarus
icarus:
	./test.py --tool icarus --max-rate 1e3 --fast

.PHONY: icarus-single-netlist
icarus-single-netlist:
	./test.py --tool icarus --single-netlist --fast

.PHONY: icarus-supernet
icarus-supernet:
	./test.py --tool icarus --supernet --max-rate 1e3 --fast

.PHONY: clean
clean:
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
	rm -f *.o *.vpi
