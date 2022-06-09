#define UART_ADDR      (void*)0x10000000
#define EXIT_CODE_ADDR (void*)0x100000
#define EXIT_CODE      0x3333

void done(int code)
{
	int* exit = EXIT_CODE_ADDR;
	*exit = code;
}

void puts(char* str, volatile int* uart)
{
	char* s = str;
	int c;
	while (c = *s++) {
		while (*uart < 0); // wait for uart to be ready
		*uart = c;
	}
}

void main()
{
	int* port = UART_ADDR;
	puts("Hello World!\n", port);
	done(EXIT_CODE);
}
