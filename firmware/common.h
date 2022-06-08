#define UART_ADDR (void*)0x10000000
#define EXIT_ADDR (void*)0x10000008

enum {
	EXIT_FAIL = 0x3333,
	EXIT_PASS = 0x5555
};
