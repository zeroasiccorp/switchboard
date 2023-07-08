SBDIR := $(shell switchboard --path)

.PHONY: python
python:
	./test.py --mode python

.PHONY: cpp
cpp: client
	./test.py --mode cpp

client: client.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

.PHONY: clean
clean:
	rm -f client
	rm -rf build obj_dir
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
