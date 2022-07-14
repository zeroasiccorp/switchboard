#include <sys/time.h>

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>
#include <sys/mman.h>
#include <stdatomic.h>
#include <sched.h>

#include "Vtestbench__Dpi.h"

#define BUFFER_ENTRIES 2000
#define PACKET_SIZE 32

static struct timeval stop_time, start_time;

int rxfd;
int txfd;

int rxptr = 0;
int txptr = 0;

typedef struct spsc_queue {
    atomic_int count;
    int packets[BUFFER_ENTRIES][32];
} spsc_queue;

spsc_queue* rxq;
spsc_queue* txq;

svLogic pi_umi_init(int rx_port, int tx_port) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "/tmp/feeds-%d", rx_port);
	rxfd = open(rx_uri, O_RDWR);

    rxq = (spsc_queue*)mmap(
        NULL,
        sizeof(spsc_queue),
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        rxfd,
        0
	);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "/tmp/feeds-%d", tx_port);
    txfd = open(tx_uri, O_RDWR);

    txq = (spsc_queue*)mmap(
        NULL,
        sizeof(spsc_queue),
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        txfd,
        0
	);

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* success, svBitVecVal* rbuf) {
    // try to receive data
    if (atomic_load(&rxq->count) > 0) {
        *success = 1;

        // read packet
        memcpy(rbuf, rxq->packets[rxptr], sizeof(int)*PACKET_SIZE);

        // update pointer
        rxptr = (rxptr+1)%BUFFER_ENTRIES;

        // update count of data
        atomic_fetch_add(&rxq->count, -1);
    } else {
        *success = 0;
    }

    // unused return value
    return 0;
}

svLogic pi_umi_send(int* success, const svBitVecVal* sbuf) {
    if (atomic_load(&txq->count) < BUFFER_ENTRIES) {
        // write data to memory
        memcpy(txq->packets[txptr], sbuf, sizeof(int)*PACKET_SIZE);

        // update pointer
        txptr = (txptr+1)%BUFFER_ENTRIES;

        // update count of data
        atomic_fetch_add(&txq->count, +1);

        // indicate succcess
        *success = 1;
    } else {
        *success = 0;
    }

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