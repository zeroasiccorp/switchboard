SBDIR := $(shell switchboard --path)

.PHONY: cpp
cpp: client
	./test.py

client: client.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

.PHONY: clean
clean:
	rm -f client
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -rf obj_dir build
