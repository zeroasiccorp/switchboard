TOOLCHAIN_PREFIX := riscv64-unknown-elf-

firmware.hex: firmware.bin
	python3 makehex.py firmware.bin 32768 > firmware.hex

firmware.bin: firmware.elf
	$(TOOLCHAIN_PREFIX)objcopy -O binary firmware.elf firmware.bin
	chmod -x $@

firmware.elf: firmware.ld firmware.s
	$(TOOLCHAIN_PREFIX)gcc -Os -mabi=ilp32 -march=rv32im -static -mcmodel=medany \
	-fvisibility=hidden -nostdlib -nostartfiles -Tfirmware.ld firmware.s -o $@

clean:
	rm -f *.bin *.elf *.hex