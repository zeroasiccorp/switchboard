#include "device.h"

void _start(void)
{
	int* port = UART_ADDR;
	puts("Hello World!\n", port);
	done(EXIT_PASS);
}
