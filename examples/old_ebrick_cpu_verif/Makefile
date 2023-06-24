EXDIR := $(abspath ..)
SBDIR := $(shell switchboard --path)

RISCV_PREFIX := riscv64-unknown-elf-

.PHONY: test
test: obj_dir/Vtestbench driver hello.bin
	./driver obj_dir/Vtestbench hello.bin

obj_dir/Vtestbench: \
	$(EXDIR)/common/verilog/picorv32.v \
	testbench.v \
	$(SBDIR)/dpi/switchboard_dpi.cc \
	$(EXDIR)/common/verilator/testbench.cc

	rm -rf obj_dir

	verilator --cc --exe -sv --trace-fst --build \
		--top-module testbench --timescale 1ns/1ps \
		-y $(SBDIR)/verilog/sim \
		-y $(EXDIR)/deps/old-umi/umi/rtl \
		-y $(EXDIR)/common/old-verilog \
		-I$(EXDIR)/deps/old-umi/umi/rtl \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "-pthread" \
		$(EXDIR)/common/verilator/config.vlt $^

driver: driver.cc $(SBDIR)/cpp/switchboard.hpp
	g++ -std=c++11 -I$(SBDIR)/cpp $< -o $@

%.bin: %.elf
	$(RISCV_PREFIX)objcopy -O binary $< $@

%.elf: %.c init.s link.ld
	$(RISCV_PREFIX)gcc -mabi=ilp32 -march=rv32im -static \
	-mcmodel=medany -fvisibility=hidden -nostdlib \
	-nostartfiles -fno-builtin -Tlink.ld $< init.s \
	-o $@

.PHONY: clean
clean:
	rm -f driver
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
	rm -f *.elf *.bin
	rm -rf obj_dir
