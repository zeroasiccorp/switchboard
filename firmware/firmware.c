#include "device.h"

void _start(void)
{
	char* msg = "Hello World from core  !";
	int id = coreid();
	msg[22] = id + '0';
	char* port = UART_ADDR;
	puts(msg, port);
	done(EXIT_PASS);
}
