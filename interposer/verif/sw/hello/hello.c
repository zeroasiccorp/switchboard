#include "device.h"

void main()
{
	char* msg = "Hello World from core  !";
	int id = coreid();
	msg[22] = id + '0';
	char* port = (void*)(OFF_CHIP | UART_ADDR);
	puts(msg, port);
	done(EXIT_PASS);
}
