#ifndef __DEVICE_H__
#define __DEVICE_H__

#include "common.h"

static inline void write_off_chip(int addr, int data) {
	int off_chip_addr;

	// compute off-chip address
	off_chip_addr = OFF_CHIP | addr;

	// write data off chip
	*((int*)off_chip_addr) = data;
}

static inline void done(int code) {
	write_off_chip(EXIT_ADDR, code);
}

static inline void puts(char* str) {
	char* s = str;
	char c;
	while (c = *s++) {
		write_off_chip(UART_ADDR, c);
	}
	write_off_chip(UART_ADDR, '\n');
}

#endif // __DEVICE_H__