/* ref: https://techroose.com/tech/spikeMulticore.html */
/* ref: https://wiki.osdev.org/RISC-V_Bare_Bones */
/* ref: https://twilco.github.io/riscv-from-scratch/2019/04/27/riscv-from-scratch-2.html */

OUTPUT_FORMAT(elf32-littleriscv)
OUTPUT_ARCH(riscv)

ENTRY(_start)

MEMORY
{
   RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 128K
}

SECTIONS
{
    . = ORIGIN(RAM);

    .text : {
        *(.text.init)
        *(.text)
    }
    .data : {
        *(.sbss)
        *(COMMON)
        *(.bss)
        *(.sdata)
        *(.rodata)
        *(.data*)
        *(.got*)
    }

    . = ALIGN(4);
    PROVIDE(__end_addr = .);

    PROVIDE(__stack_top = ORIGIN(RAM) + LENGTH(RAM));
}
