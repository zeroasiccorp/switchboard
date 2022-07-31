#include "device.h"

void main() {
	// read information from memory
	int row = *((volatile int*)ROW_ADDR);
	int col = *((volatile int*)COL_ADDR);
	int rows = *((volatile int*)ROWS_ADDR);
	int cols = *((volatile int*)COLS_ADDR);

	// format message
	char msg [] = "Hello from (x, x)!";
	msg[12] = '0' + row;
	msg[15] = '0' + col;

	// print message if this is the southeast corner
	if ((row==(rows-1)) && (col==(cols-1))) {
		puts(0, 0, msg);
		done(0, 0, EXIT_PASS);
	}
}