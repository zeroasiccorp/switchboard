#include <sys/time.h>
#include <stdio.h>
#include <string.h>

#include "spsc_queue.h"
#include "Vtestbench__Dpi.h"

static struct timeval stop_time, start_time;
static spsc_queue* rxq;
static spsc_queue* txq;
static uint32_t rxp[SPSC_QUEUE_PACKET_SIZE];
static uint32_t txp[SPSC_QUEUE_PACKET_SIZE];

svLogic pi_umi_init(int rx_port, int tx_port) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "/tmp/feeds-%d-r", rx_port);
    rxq = spsc_open(rx_uri);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "/tmp/feeds-%d-w", tx_port);
    txq = spsc_open(tx_uri);

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* success, svBitVecVal* rbuf){
    *success = spsc_recv(rxq, rbuf);
    return 0;
}

svLogic pi_umi_send(int* success, const svBitVecVal* sbuf) {
    *success = spsc_send(txq, sbuf);
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