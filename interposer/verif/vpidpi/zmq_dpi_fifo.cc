#include <sys/time.h>

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>

#include "Vtestbench__Dpi.h"

static struct timeval stop_time, start_time;

int rxfd;
int txfd;

svLogic pi_umi_init(int rx_port, int tx_port) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "/tmp/feeds-%d", rx_port);

    // setup RX port
    if((mkfifo(rx_uri, S_IRWXU | S_IRWXG)) < 0){
        printf("Error creating named pipe, assuming that it exists already...\n");
    } else {
        printf("Named pipe %s created.\n", rx_uri);
    }

    rxfd = open(rx_uri, O_RDONLY | O_NONBLOCK);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "/tmp/feeds-%d", tx_port);

    // TX port
    if((mkfifo(tx_uri, S_IRWXU | S_IRWXG)) < 0){
        printf("Error creating named pipe, assuming that it exists already...\n");
    } else {
        printf("Named pipe %s created.\n", tx_uri);
    }    
    txfd = open(tx_uri, O_WRONLY);

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* got_packet, svBitVecVal* rbuf) {
    // try to receive data
    uint8_t buf[32];
    int bytes_read;
    bytes_read = read(rxfd, buf, 32);
    if (bytes_read > 0) {
        // finish reading the packet if needed
        while(bytes_read < 32){
            bytes_read += read(rxfd, buf+bytes_read, 32-bytes_read);
        }

        // copy out data
        *got_packet = 1;
        for (int i=0; i<32; i++) {
            rbuf[i] = buf[i];
        }
    } else {
        *got_packet = 0;
    }

    // unused return value
    return 0;
}

svLogic pi_umi_send(const svBitVecVal* sbuf) {
    // copy data into a buffer.  we can't directly use sbuf
    // with zmq_send, because it is an array of uint32_t
    uint8_t buf[32];
    for (int i=0; i<32; i++) {
        buf[i] = sbuf[i];
    }

    // send message
    write(txfd, buf, sizeof(buf));

    // unused return value
    return 0;
}

svLogic pi_time_taken(double* t) {
    // compute time taken in seconds
	gettimeofday(&stop_time, NULL);
    unsigned long t_us = 0;
    t_us += ((stop_time.tv_sec - start_time.tv_sec) * 1000000);
    t_us += (stop_time.tv_usec - start_time.tv_usec);
    *t = 1.0e-6*t_us;
    gettimeofday(&start_time, NULL);

    // unused return value
    return 0;
}