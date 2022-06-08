#include "common.h"

static inline void done(int code)
{
	int* exit = EXIT_ADDR;
	*exit = code;
}

static inline void puts(char* str, volatile int* uart)
{
	char* s = str;
	int c;
	while (c = *s++) {
		while (*uart < 0); // wait for uart to be ready
		*uart = c;
	}
}

int tohost, fromhost; // These are only defined to quiet Spike
