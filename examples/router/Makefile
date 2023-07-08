SBDIR := $(shell switchboard --path)

.PHONY: cpp
cpp: client $(SBDIR)/cpp/router
	./test.py

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
