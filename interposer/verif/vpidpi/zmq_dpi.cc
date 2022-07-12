#include <sys/time.h>

// ZMQ stuff
#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>
#include<pthread.h>

#include "Vtestbench__Dpi.h"

int rx_port_arg;  // TODO clean this up
bool rx_data_valid = false;
bool rx_data_accepted = false;
uint8_t zmq_global_buf[32];
pthread_t rx_tid;
pthread_mutex_t rx_lock = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t rx_cond = PTHREAD_COND_INITIALIZER;

static void *context = NULL;
static void *rx_socket = NULL;
static void *tx_socket = NULL;
static struct timeval stop_time, start_time;

void* rx_thread(void *arg) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "tcp://*:%d", rx_port_arg);

    // setup RX port
    rx_socket = zmq_socket (context, ZMQ_REP);
    int rcrx = zmq_bind (rx_socket, rx_uri);
    assert (rcrx == 0);

    while (1) {
        // receive data
        uint8_t buf[32];
        zmq_recv(rx_socket, buf, 32, 0);

        // acknowledge receipt of data
        zmq_send(rx_socket, NULL, 0, 0);

        // transfer data, indicate that it is ready,
        // and wait for the data to be accepted
        pthread_mutex_lock(&rx_lock);
        rx_data_valid = true;
        for (int i=0; i<32; i++) {
            zmq_global_buf[i] = buf[i];
        }
        while(!rx_data_accepted) {
            pthread_cond_wait(&rx_cond, &rx_lock);
        }
        rx_data_accepted = false;
        pthread_mutex_unlock(&rx_lock);
    }

    return NULL;
}

svLogic pi_umi_init(int rx_port, int tx_port) {
    // create ZMQ context
    context = zmq_ctx_new ();

    // create RX thread
    rx_port_arg = rx_port;
    pthread_create(&rx_tid, NULL, &rx_thread, NULL);

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
    // try to receive data
    pthread_mutex_lock(&rx_lock);
    if (rx_data_valid) {
        // copy out data
        *got_packet = 1;
        for (int i=0; i<32; i++) {
            rbuf[i] = zmq_global_buf[i];
        }

        // signaling to RX thread
        rx_data_valid = false;
        rx_data_accepted = true;
        pthread_cond_signal(&rx_cond);
    } else {
        *got_packet = 0;
    }
    pthread_mutex_unlock(&rx_lock);

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