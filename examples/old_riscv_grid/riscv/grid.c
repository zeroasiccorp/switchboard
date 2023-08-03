#include "device.h"

void main() {
    // read information from memory
    int __memory_top = (1 << 17);
    unsigned int row = *((volatile unsigned int*)(MEMORY_TOP - 4));
    unsigned int col = *((volatile unsigned int*)(MEMORY_TOP - 8));
    unsigned int rows = *((volatile unsigned int*)(MEMORY_TOP - 12));
    unsigned int cols = *((volatile unsigned int*)(MEMORY_TOP - 16));

    // format message
    char msg[] = "Hello from (x, x)!";
    msg[12] = '0' + row;
    msg[15] = '0' + col;

    // print message if this is the southeast corner
    if ((row == (rows - 1)) && (col == (cols - 1))) {
        puts(0, 0, msg);
        done(0, 0, EXIT_PASS);
    }
}