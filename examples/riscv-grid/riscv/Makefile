RISCV_PREFIX := riscv64-unknown-elf-
GCC := $(RISCV_PREFIX)gcc
OBJCOPY := $(RISCV_PREFIX)objcopy

%.bin: %.elf
	$(OBJCOPY) \
	-O binary \
	$< \
	$@

%.elf: %.c device.h init.s link.ld
	$(GCC) \
	-O3 \
	-mabi=ilp32 \
	-march=rv32im \
	-static \
	-mcmodel=medany \
	-fvisibility=hidden \
	-nostdlib \
	-nostartfiles \
	-fno-builtin \
	-I. \
	-Tlink.ld \
	$< init.s \
	-o $@

.PHONY: clean
clean:
	rm -f *.elf *.bin