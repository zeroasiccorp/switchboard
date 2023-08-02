#include "device.h"

void main() {
    // read information from memory
    unsigned int row = *((volatile unsigned int*)(MEMORY_TOP - 4));
    unsigned int col = *((volatile unsigned int*)(MEMORY_TOP - 8));
    unsigned int rows = *((volatile unsigned int*)(MEMORY_TOP - 12));
    unsigned int cols = *((volatile unsigned int*)(MEMORY_TOP - 16));
    unsigned int target = *((volatile unsigned int*)(MEMORY_TOP - 20));

    // pointer to memory that will be written by other CPUs
    volatile unsigned int* mail_ptr = ((volatile unsigned int*)((MEMORY_TOP - 24)));

    // initialize mailbox to a non-zero
    // value if we're the first processor,
    // noting that the client is at (0, 0)
    if ((row == 0) && (col == 1)) {
        *mail_ptr = 1;
    }

    // determine where mail will be sent
    int next_row = row;
    int next_col = col + 1;
    if (next_col == cols) {
        // move to the next row
        next_col = 0;
        next_row = row + 1;
        if (next_row == rows) {
            // send back to the beginning
            next_row = 0;
            next_col = 1;
        }
    }

    // format message to be sent back to the client if
    // the mail received matches a certain value
    char msg[] = "Hello from (x, x)!";
    msg[12] = '0' + row;
    msg[15] = '0' + col;

    unsigned int prev_mail = 0, mail;
    while (1) {
        // blocking mail read
        do {
            mail = *mail_ptr;
        } while (mail == prev_mail);
        prev_mail = mail;

        if (mail == target) {
            break;
        } else {
            write_off_chip(next_row, next_col, (int)mail_ptr, mail + 1);
        }
    }

    puts(0, 0, msg);
    done(0, 0, EXIT_PASS);
}