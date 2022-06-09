OUTPUT_FORMAT(elf32-littleriscv)
OUTPUT_ARCH(riscv)

ENTRY( _start )

SECTIONS
{
  . = 0x80000000;
  .text : {
		*(.text)
	}
	.data ALIGN(8): {
		*(.sbss)
		*(COMMON)
		*(.bss)
		*(.rodata)
		*(.data*)
	}
}
