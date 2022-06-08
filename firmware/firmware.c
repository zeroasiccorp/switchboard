/*
.section .text

.global _start
_start: la a0, msg              # a0 = address of msg
        li a1, 0x10000000       # a1 = address of output port

puts:   lbu a2, (a0)            # a2 = load unsigned byte from string
        beqz a2, done           # if byte is null, break the loop

uwait:  lw a3, (a1)             # wait for UART to be ready
        bltz a3, uwait

        sw a2, (a1)             # send byte to output

        addi a0, a0, 1          # increment message pointer and repeat
        j puts

done:   li a0, 0x100000         # shut down the machine
        li a1, 0x3333           # compute as (EXIT_CODE << 16) | 0x3333
        sw a1, (a0)

.section .rodata
msg:
     .string "Hello World!\n"
*/

#define UART_ADDR      (void*)0x10000000
#define EXIT_CODE_ADDR (void*)0x100000
#define EXIT_CODE      0x3333

char* msg = "Hello World!\n";

void __attribute__((__noreturn__)) done(void)
{
	int* exit = EXIT_CODE_ADDR;
	int code = EXIT_CODE;
	*exit = code;
	while(1);
}

static inline void __attribute__((__noreturn__)) z_puts(char* str, volatile int* uart)
{
	char* s = str;
	int c;
	while (c = *s++) {
		while (*uart < 0); // wait for uart to be ready
		*uart = c;
	}
	done();
}

void _start(void)
{
	char* s = msg;
	int* port = UART_ADDR;
	z_puts(s, port);
}

