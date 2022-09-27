.PHONY: hello
hello: prereqs
	make -C riscv hello.bin
	./scripts/grid.py --binfile riscv/hello.bin --rows 1 --cols 2

.PHONY: grid
grid: prereqs
	make -C riscv grid.bin
	./scripts/grid.py

# not working
.PHONY: addloop
addloop: prereqs
	make -C riscv addloop.bin
	./scripts/grid.py --rows 2 --cols 3 --binfile riscv/addloop.bin --params 1000 0

.PHONY: prereqs
prereqs:
	make -C ../../cpp router
	make -C cpp client
	make -C verilator obj_dir/Vtestbench

.PHONY: clean
clean:
	make -C riscv clean
	make -C cpp clean
	make -C verilator clean
