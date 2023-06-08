SBDIR := $(shell switchboard --path)

.PHONY: umidriver
umidriver: prereqs
	$(SBDIR)/cpp/umidriver --sim verilator/obj_dir/Vtestbench --txfile in.memh --rxfile expect.memh

.PHONY: prereqs
prereqs:
	make -C $(SBDIR)/cpp umidriver
	make -C verilator obj_dir/Vtestbench

.PHONY: clean
clean:
	make -C $(SBDIR)/cpp clean
	make -C verilator clean
	rm -f queue-*
