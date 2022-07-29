#ifndef __DEVICE_H__
#define __DEVICE_H__

#define OFF_CHIP  0x80000000
#define UART_ADDR 0x10000000
#define EXIT_ADDR 0x10000008
#define GPIO_ADDR 0x20000000
#define EXIT_FAIL 0x3333
#define EXIT_PASS 0x5555

static inline void write_off_chip(int addr, int data) {
	int off_chip_addr;

	// compute off-chip address
	off_chip_addr = OFF_CHIP | addr;

	// write data off chip
	*((volatile int*)off_chip_addr) = data;
}

static inline void done(int code) {
	write_off_chip(EXIT_ADDR, code);
}

static inline void puts(char* str) {
	char* s = str;
	char c;
	while ((c = *s++)) {
		write_off_chip(UART_ADDR, c);
	}
	write_off_chip(UART_ADDR, '\n');
}

#endif // __DEVICE_H__