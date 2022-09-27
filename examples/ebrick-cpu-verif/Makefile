.PHONY: hello
hello:
	make -C riscv hello.bin
	make -C cpp driver
	make -C verilator
	./cpp/driver verilator/obj_dir/Vtestbench riscv/hello.bin

.PHONY: clean
clean:
	make -C riscv clean
	make -C cpp clean
	make -C verilator clean
