#include <sys/time.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "umi_intf.h"
#include "Vtestbench__Dpi.h"

static struct timeval stop_time, start_time;
static spsc_queue* rxq;
static spsc_queue* txq;

svLogic pi_umi_init(int rx_port, int tx_port, int mode) {
    // determine URIs
    char rx_uri[128];
    char tx_uri[128];
    if (mode == UMI_QUEUE) {
        sprintf(rx_uri, "/tmp/feeds-%d", rx_port);
        sprintf(tx_uri, "/tmp/feeds-%d", tx_port);
    } else if (mode == UMI_TCP) {
        sprintf(rx_uri, "127.0.0.1:%d", rx_port);
        sprintf(tx_uri, "127.0.0.1:%d", tx_port);
    } else {
        fprintf(stderr, "Unknown interface mode.\n");
        exit(1);
    }

    rxq = umi_init(rx_uri, false, (umi_mode)mode);
    txq = umi_init(tx_uri, true, (umi_mode)mode);

    // return unused value
    return 0;
}

svLogic pi_umi_recv(int* success, svBitVecVal* rbuf){
    *success = spsc_recv(rxq, (uint8_t*)rbuf, 32);
    return 0;
}

svLogic pi_umi_send(int* success, const svBitVecVal* sbuf) {
    *success = spsc_send(txq, (uint8_t*)sbuf, 32);
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