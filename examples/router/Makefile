.PHONY: hello
hello: prereqs
	./scripts/test.py

.PHONY: prereqs
prereqs:
	make -C ../../cpp router	
	make -C cpp client
	make -C verilator obj_dir/Vtestbench

.PHONY: clean
clean:
	make -C cpp clean
	make -C verilator clean
	rm -f queue-*
