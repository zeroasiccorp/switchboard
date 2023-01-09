.PHONY: hello
hello: prereqs
	./scripts/test.py

.PHONY: prereqs
prereqs:
	make -C verilator obj_dir/Vtestbench

.PHONY: clean
clean:
	make -C verilator clean
	rm -f queue-*
	rm -f *.vcd
