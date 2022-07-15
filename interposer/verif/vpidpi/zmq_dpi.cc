#include <sys/time.h>

#include "spsc_queue.hpp"
#include "Vtestbench__Dpi.h"

static struct timeval stop_time, start_time;
static bip::managed_shared_memory rxs;
static bip::managed_shared_memory txs;
ring_buffer* rxq;
ring_buffer* txq;

packet rxp;
packet txp;

svLogic pi_umi_init(int rx_port, int tx_port) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "shmem-%d", rx_port);
    rxq = spsc_open(rxs, rx_uri);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "shmem-%d", tx_port);
    txq = spsc_open(txs, tx_uri);
    txq->reset();

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* success, svBitVecVal* rbuf){
    *success = rxq->pop(rxp) ? 1 : 0;
    if (*success) {
        for (int i=0; i<PACKET_SIZE; i++){
            rbuf[i] = rxp[i];
        }
    }
    return 0;
}

svLogic pi_umi_send(int* success, const svBitVecVal* sbuf) {
    for (int i=0; i<PACKET_SIZE; i++){
        txp[i] = sbuf[i];
    }
    *success = txq->push(txp) ? 1 : 0;
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