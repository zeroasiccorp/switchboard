.PHONY: umidriver
umidriver: prereqs
	../../cpp/umidriver --sim verilator/obj_dir/Vtestbench --txfile in.memh --rxfile expect.memh

.PHONY: prereqs
prereqs:
	make -C ../../cpp umidriver
	make -C verilator obj_dir/Vtestbench

.PHONY: clean
clean:
	make -C ../../cpp clean
	make -C verilator clean
	rm -f queue-*
