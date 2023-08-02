#ifndef __DEVICE_H__
#define __DEVICE_H__

#define OFF_CHIP 0x80000000
#define GPIO_ADDR 0x400000
#define UART_ADDR 0x500000
#define EXIT_ADDR 0x600000
#define EXIT_FAIL 0x3333
#define EXIT_PASS 0x5555

// TODO: consider defining in the linker script
#define MEMORY_TOP 0x20000

static inline void write_off_chip(int row, int col, int addr, int data) {
    int off_chip_addr;

    // compute off-chip address
    off_chip_addr = 0;
    off_chip_addr |= (1 & 0x1) << 31;
    off_chip_addr |= (row & 0xf) << 27;
    off_chip_addr |= (col & 0xf) << 23;
    off_chip_addr |= (addr & 0x7fffff) << 0;

    // write data off chip
    *((volatile int*)off_chip_addr) = data;
}

static inline void done(int row, int col, int code) {
    write_off_chip(row, col, EXIT_ADDR, code);
}

static inline void puts(int row, int col, char* str) {
    char* s = str;
    char c;
    while ((c = *s++)) {
        write_off_chip(row, col, UART_ADDR, c);
    }
    write_off_chip(row, col, UART_ADDR, '\n');
}

#endif // __DEVICE_H__