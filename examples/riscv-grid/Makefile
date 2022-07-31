.PHONY: hello
hello: prereqs
	make -C riscv hello.bin
	./scripts/hello.py

.PHONY: grid
grid: prereqs
	make -C riscv grid.bin
	./scripts/grid.py

# not working
.PHONY: addloop
addloop: prereqs
	make -C riscv addloop.bin
	./scripts/grid.py --binfile riscv/addloop.bin

.PHONY: prereqs
prereqs:
	make -C cpp client
	make -C verilator obj_dir/Vtestbench
	make -C ../../models router

.PHONY: clean
clean:
	make -C riscv clean
	make -C cpp clean
	make -C verilator clean