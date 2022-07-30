UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SHMEM_FILES := /tmp/boost_interprocess/queue-*
else
	SHMEM_FILES := /dev/shm/queue-*
endif

.PHONY: hello
hello:
	make -C riscv hello.bin
	make -C cpp client
	make -C verilator obj_dir/Vtestbench
	rm -f $(SHMEM_FILES)
	./scripts/hello.sh

.PHONY: daisy
daisy:
	make -C riscv daisy.bin
	make -C cpp client
	make -C verilator obj_dir/Vtestbench
	rm -f $(SHMEM_FILES)
	./scripts/daisy.py

.PHONY: clean
clean:
	make -C riscv clean
	make -C cpp clean
	make -C verilator clean