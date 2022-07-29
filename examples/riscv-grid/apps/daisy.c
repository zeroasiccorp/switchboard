#include "device.h"

#define LAST_CHIP 9
#define MSG_SIZE 32

// data passed from one chip to the next
int chip_id = 0;
char msg[MSG_SIZE] = {0};

extern int __end_addr;  // linker symbol: end address of text and data

void main() {
	// append the chip_id to the message
	for (int i=0; i<=(MSG_SIZE-3); i++){
		if (msg[i] == '\0'){
			msg[i] = '0' + chip_id;
			msg[i+1] = ' ';
			msg[i+2] = '\0';
			break;
		}
	}

	// program next chip, unless this is the last chip,
	// in which case the message should be printed

	if (chip_id != LAST_CHIP) {
		// increment the chip ID to pass onto the next chip
		chip_id++;

		// hold next chip in reset
		write_off_chip(GPIO_ADDR, 0);

		// copy the program and data contents, word by word
		for (int i=0; i<((int)(&__end_addr)); i+=4) {
			write_off_chip(i, *((int*)i));
		}

		// release reset
		write_off_chip(GPIO_ADDR, 1);
	} else {
		// write message
		puts(msg);
		done(EXIT_PASS);
	}
}
