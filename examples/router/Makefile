# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

SBDIR := $(shell switchboard --path)

.PHONY: verilator
verilator: client $(SBDIR)/cpp/router
	./test.py --tool verilator

.PHONY: icarus
icarus: client $(SBDIR)/cpp/router
	./test.py --tool icarus

$(SBDIR)/cpp/router:
	make -C $(SBDIR)/cpp router

client: client.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

.PHONY: clean
clean:
	rm -f client
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
