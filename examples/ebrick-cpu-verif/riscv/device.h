#ifndef __DEVICE_H__
#define __DEVICE_H__

#define UART_ADDR 0x500000
#define EXIT_ADDR 0x600000
#define EXIT_FAIL 0x3333
#define EXIT_PASS 0x5555

static inline void done(int code) {
	*((volatile int*)EXIT_ADDR) = code;
}

static inline void puts(char* str) {
	char* s = str;
	char c;
	while ((c = *s++)) {
		*((volatile int*)UART_ADDR) = c;
	}
	*((volatile int*)UART_ADDR) = '\n';
}

#endif // __DEVICE_H__
