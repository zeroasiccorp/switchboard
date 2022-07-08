#include <sys/time.h>

// ZMQ stuff
#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>

#include "Vtestbench__Dpi.h"

static void *context = NULL;
static void *rx_socket = NULL;
static void *tx_socket = NULL;
static struct timeval stop_time, start_time;

svLogic pi_umi_init(int rx_port, int tx_port) {
    // create ZMQ context
    context = zmq_ctx_new ();

    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "tcp://*:%d", rx_port);

    // setup RX port
    rx_socket = zmq_socket (context, ZMQ_REP);
    int rcrx = zmq_bind (rx_socket, rx_uri);
    assert (rcrx == 0);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "tcp://localhost:%d", tx_port);

    // TX port
    tx_socket = zmq_socket (context, ZMQ_REQ);
    int rctx = zmq_connect (tx_socket, tx_uri);
    assert (rctx == 0);

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* got_packet, svBitVecVal* rbuf) {
    // make sure that RX socket has started
    assert(rx_socket);

    // try to receive data
    uint8_t buf[32];
    int nrecv = zmq_recv(rx_socket, buf, 32, ZMQ_NOBLOCK);

    if (nrecv == 32) {
        *got_packet = 1;

        // acknowledge receipt of data
        zmq_send(rx_socket, NULL, 0, 0);

        // copy data into the output buffer.  we can't directly
        // use rbuf with zmq_recv because it is an array of uint32_t
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
    // make sure that TX socket has started
    assert(tx_socket);

    // copy data into a buffer.  we can't directly use sbuf
    // with zmq_send, because it is an array of uint32_t
    uint8_t buf[32];
    for (int i=0; i<32; i++) {
        buf[i] = sbuf[i];
    }

    // send message
    zmq_send(tx_socket, buf, 32, 0);
	zmq_recv(tx_socket, NULL, 0, 0);

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