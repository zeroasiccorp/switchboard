# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

.PHONY: verilator
verilator:
	./test.py --tool verilator --trace

.PHONY: icarus
icarus:
	./test.py --tool icarus --trace

.PHONY: clean
clean:
	rm -f queue-* *.q
	rm -f *.mt0 *.wrapper* *.o *.vpi
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
