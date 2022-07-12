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

#define BUFFER_SIZE 4096
#define BUFFER_ENTRIES 100
#define PACKET_SIZE 32

static struct timeval stop_time, start_time;

int rxfd;
int txfd;

int rxptr = 0;
int txptr = 0;

atomic_int* rxmem;
atomic_int* txmem;

svLogic pi_umi_init(int rx_port, int tx_port) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "/tmp/feeds-%d", rx_port);
	rxfd = open(rx_uri, O_RDWR | O_CREAT, 0666);
    ftruncate(rxfd, BUFFER_SIZE);

    rxmem = (atomic_int*)mmap(
        NULL,
        BUFFER_SIZE,
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        rxfd,
        0
	);
    atomic_store(rxmem, 0);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "/tmp/feeds-%d", tx_port);
    txfd = open(tx_uri, O_RDWR | O_CREAT, 0666);
    ftruncate(txfd, BUFFER_SIZE);

    txmem = (atomic_int*)mmap(
        NULL,
        BUFFER_SIZE,
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        txfd,
        0
	);
    atomic_store(txmem, 0);

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* got_packet, svBitVecVal* rbuf) {
    // try to receive data
    if (atomic_load(rxmem) > 0) {
        *got_packet = 1;

        // read packet
        // TODO: change to memcpy
        int off = 1+PACKET_SIZE*rxptr;
        for (int i=0; i<PACKET_SIZE; i++) {
            rbuf[i] = rxmem[off+i];
        }

        // update pointer
        rxptr = (rxptr+1)%BUFFER_ENTRIES;

        // update count of data
        atomic_fetch_add(rxmem, -1);
    } else {
        *got_packet = 0;
    }

    // unused return value
    return 0;
}

svLogic pi_umi_send(const svBitVecVal* sbuf) {
    while(atomic_load(txmem) >= BUFFER_ENTRIES) {
        sched_yield();
    }

    // write data to memory
    int off = 1+PACKET_SIZE*txptr;
    for (int i=0; i<32; i++) {
        txmem[off+i] = sbuf[i];
    }

    // update pointer
    txptr = (txptr+1)%BUFFER_ENTRIES;

    // update count of data
    atomic_fetch_add(txmem, +1);

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