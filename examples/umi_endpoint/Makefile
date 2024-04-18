# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

.PHONY: verilator
verilator:
	./test.py --tool verilator

.PHONY: icarus
icarus:
	./test.py --tool icarus

.PHONY: clean
clean:
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
