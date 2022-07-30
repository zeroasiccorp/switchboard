.PHONY: hello
hello:
	make -C riscv hello.bin
	make -C cpp client
	make -C verilator obj_dir/Vtestbench
	./scripts/hello.sh

.PHONY: daisy
daisy:
	make -C riscv daisy.bin
	make -C cpp client
	make -C verilator obj_dir/Vtestbench
	./scripts/daisy.py

.PHONY: clean
clean:
	make -C riscv clean
	make -C cpp clean
	make -C verilator clean