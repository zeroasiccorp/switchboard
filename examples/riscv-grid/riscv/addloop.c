#include "device.h"

void main() {
	// read information from memory
	int row = *((volatile int*)ROW_ADDR);
	int col = *((volatile int*)COL_ADDR);
	int rows = *((volatile int*)ROWS_ADDR);
	int cols = *((volatile int*)COLS_ADDR);

	// initialize mailbox to a non-zero
	// value if we're the first processor,
	// noting that the client is at (0, 0)
	if ((row == 0) && (col == 1)) {
		*((volatile int*)MAIL_ADDR) = 1;
	}

	int prev_mail = 0;
	while (1) {
		// blocking mail read
		int mail;
		do {
			mail = *((volatile int*)MAIL_ADDR);
		} while (mail == prev_mail);
		prev_mail = mail;

		int next_mail;
		if (mail == 10) {
			// if the mail value hits a certain threshold,
			// send a message back to the client and stop
			char msg [] = "Hello from (x, x)!";
			msg[12] = '0' + row;
			msg[15] = '0' + col;
			puts(0, 0, msg);
			done(0, 0, EXIT_PASS);
			break;
		} else {
			// otherwise increment the mail value
			next_mail = mail + 1;
		}

		// calc where the new mail value will be sent
		int next_col, next_row;
		if (col == (cols-1)) {
			if (row == (rows-1)) {
				// if we get here, that means the processor is in
				// the southeast corner, so send mail back to the
				// first processor
				next_row = 0;
				next_col = 1;
			} else {
				// if we get here, it means the processor is on
				// the eastern edge (but not at the bottom), so
				// increment the row and reset the column
				next_row = row+1;
				next_col = 0;
			}
		} else {
			// otherwise we're in the middle of a row,
			// so simply increment the column
			next_row = row;
			next_col = col+1;
		}

		// send the new mail to the calculated address
		write_off_chip(next_row, next_col, MAIL_ADDR, next_mail);
	}
}