TOOLCHAIN_PREFIX ?= riscv64-unknown-elf-
SPIKE_INCLUDE_DIR ?= /usr/local/include

.PHONY: qemu spike clean

# OS-specific behavior
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SHARED_FLAGS := -bundle -undefined dynamic_lookup
else
	SHARED_FLAGS := -shared
endif

firmware.hex: firmware.bin
	python3 makehex.py firmware.bin 32768 > firmware.hex

firmware.bin: firmware.elf
	$(TOOLCHAIN_PREFIX)objcopy -O binary firmware.elf firmware.bin
	chmod -x $@

firmware.elf: firmware.ld firmware.c
	$(TOOLCHAIN_PREFIX)gcc -Os -mabi=ilp32 -march=rv32imc -static -mcmodel=medany \
	-fvisibility=hidden -nostdlib -nostartfiles -fno-builtin -Tfirmware.ld init.s firmware.c -o $@

qemu: firmware.bin
	qemu-system-riscv32 -nographic -machine virt -bios none -kernel firmware.bin

spike: uart_plugin.so exit_plugin.so firmware.elf
	spike -m1 --isa=RV32IMC \
	--extlib=uart_plugin.so --device=uart_plugin,0x10000000,argument \
	--extlib=exit_plugin.so --device=exit_plugin,0x10000008,argument \
	firmware.elf

%.so: %.c
	gcc -I $(SPIKE_INCLUDE_DIR) -Os $(SHARED_FLAGS) -o $@ -Wall -Werror -fPIC $<

clean:
	rm -f *.bin *.elf *.hex *.so
