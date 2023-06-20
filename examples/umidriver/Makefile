SBDIR := $(shell switchboard --path)

.PHONY: umidriver
umidriver: prereqs
	$(SBDIR)/cpp/old_umidriver --sim verilator/obj_dir/Vtestbench --txfile in.memh --rxfile expect.memh

.PHONY: prereqs
prereqs:
	make -C $(SBDIR)/cpp old_umidriver
	make -C verilator obj_dir/Vtestbench

.PHONY: clean
clean:
	make -C $(SBDIR)/cpp clean
	make -C verilator clean
	rm -f queue-*
