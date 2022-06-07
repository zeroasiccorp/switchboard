OUTPUT_FORMAT(elf32-littleriscv)
OUTPUT_ARCH(riscv)

ENTRY( _start )

SECTIONS
{
  . = 0x80000000;
  .text : { *(.text) }
  .rodata : { *(.rodata) }
}
