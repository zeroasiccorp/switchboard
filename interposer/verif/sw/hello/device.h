#include "common.h"

static inline void delay(unsigned int nops)
{
	for (unsigned int n = nops; n; n--) __asm__ ("nop");
}

static inline void done(int code)
{
	int* exit = (void*)EXIT_ADDR;
	delay(5000);
	*exit = code;
}

static inline void puts(char* str, volatile char* uart)
{
	char* s = str;
	char c;
	while (c = *s++) {
		while (*uart < 0);
		*uart = c;
	}
	while (*uart < 0);
	*uart = '\n';
}

static inline int coreid()
{
	int id = -1;
#if 0
	asm volatile(
		"csrr %0, mhartid"
		: "=r"(id) : :
	);
#else
	id = 0;
#endif
	return id;
}

long long int tohost, fromhost; // These are only defined to quiet Spike
