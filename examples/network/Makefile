# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

.PHONY: verilator
verilator:
	./test.py --tool verilator --start-delay 1 --max-rate 1e3

.PHONY: verilator-netlist
verilator-netlist:
	./test.py --tool verilator --start-delay 1 --max-rate 1e3 --netlist

.PHONY: icarus
icarus:
	./test.py --tool icarus --start-delay 1 --max-rate 1e3

.PHONY: icarus-netlist
icarus-netlist:
	./test.py --tool icarus --start-delay 1 --max-rate 1e3 --netlist

.PHONY: clean
clean:
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
	rm -f *.o *.vpi
