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
		*((volatile unsigned int*)MAIL_ADDR) = (1 << 31) | (1 << 30) | 1;
	}

	unsigned int prev_mail;
	prev_mail = 0;
	while (1) {
		// blocking mail read
		unsigned int mail;
		do {
			mail = *((volatile unsigned int*)MAIL_ADDR);
		} while (mail == prev_mail);
		prev_mail = mail;

		if ((mail & 0x3fffffff) == 1000) {
			// if the mail value hits a certain threshold,
			// send a message back to the client and stop
			char msg [] = "Hello from (x, x)!";
			msg[12] = '0' + row;
			msg[15] = '0' + col;
			puts(0, 0, msg);
			done(0, 0, EXIT_PASS);
			break;
		}

		// determine what direction the message is moving

		int send_right, send_down;
		if ((col == 1) && (row == 0)) {
			send_right = 1;
			send_down = 1;
		} else {
			send_right = (mail >> 31) & 1;
			send_down = (mail >> 30) & 1;
		}

		// figure out the destination of the mail

		int next_col = col;
		if (send_right) {
			next_col++;
		} else {
			next_col--;
		}

		int next_row = row;
		if ((next_col == -1) || (next_col == cols)) {
			// keep same column address and flip direction
			next_col = col;
			send_right = 1 - send_right;

			// move to next row
			if (send_down) {
				next_row++;	
			} else {
				next_row--;
			}

			// see if we went off the grid
			if (next_row == rows) {
				next_row = row;
				if (next_col == 0) {
					// on the left edge
					next_col = 1;
				} else {
					// on the right edge
					next_col = cols - 2;
				}
				send_down = 0;
			}
		}

		// determine mail to be sent
		unsigned int next_mail;
		next_mail = 0;
		next_mail |= (send_right << 31);
		next_mail |= (send_down  << 30);
		next_mail |= ((mail + 1) & 0x3fffffff);

		// send the new mail to the calculated address
		write_off_chip(next_row, next_col, MAIL_ADDR, next_mail);
	}
}