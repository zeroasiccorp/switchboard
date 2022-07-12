#include <sys/time.h>

// ZMQ stuff
#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>
#include<pthread.h>

#include "Vtestbench__Dpi.h"
#define BUFSIZE 100

int rx_port_arg;  // TODO clean this up
bool rx_data_valid = false;
bool rx_data_accepted = false;
uint8_t zmq_buf[BUFSIZE][32];
int buf_fill_ptr = 0;
int buf_use_ptr = 0;
int buf_count = 0;
pthread_t rx_tid;
pthread_mutex_t buf_lock = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t buf_empty = PTHREAD_COND_INITIALIZER;

static void *context = NULL;
static void *rx_socket = NULL;
static void *tx_socket = NULL;
static struct timeval stop_time, start_time;

void* rx_thread(void *arg) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "ipc:///tmp/feeds-%d", rx_port_arg);

    // setup RX port
    rx_socket = zmq_socket (context, ZMQ_DEALER);
    int rcrx = zmq_bind (rx_socket, rx_uri);
    assert (rcrx == 0);

    while (1) {
        // receive data
        uint8_t buf[32];
        zmq_recv(rx_socket, buf, 32, 0);

        // transfer data, indicate that it is ready,
        // and wait for the data to be accepted
        pthread_mutex_lock(&buf_lock);

        // wait for space
        while(buf_count == BUFSIZE) {
            pthread_cond_wait(&buf_empty, &buf_lock);
        }

        // put data
        for (int i=0; i<32; i++) {
            zmq_buf[buf_fill_ptr][i] = buf[i];
        }
        buf_fill_ptr = (buf_fill_ptr+1) % BUFSIZE;
        buf_count++;

        pthread_mutex_unlock(&buf_lock);
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
    sprintf(tx_uri, "ipc:///tmp/feeds-%d", tx_port);

    // TX port
    tx_socket = zmq_socket (context, ZMQ_DEALER);
    int rctx = zmq_connect (tx_socket, tx_uri);
    assert (rctx == 0);

    // unused return value
    return 0;
}

svLogic pi_umi_recv(int* got_packet, svBitVecVal* rbuf) {
    // try to receive data
    pthread_mutex_lock(&buf_lock);
    if (buf_count > 0) {
        // copy out data
        *got_packet = 1;
        for (int i=0; i<32; i++) {
            rbuf[i] = zmq_buf[buf_use_ptr][i];
        }
        buf_use_ptr = (buf_use_ptr + 1)% BUFSIZE;
        buf_count--;

        // signaling to RX thread
        pthread_cond_signal(&buf_empty);
    } else {
        *got_packet = 0;
    }
    pthread_mutex_unlock(&buf_lock);

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