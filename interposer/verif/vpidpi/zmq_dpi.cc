#include <sys/time.h>

// ZMQ stuff
#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>

#include "Vtestbench__Dpi.h"

static void *context = NULL;
static void *socket = NULL;
static struct timeval stop_time, start_time;

static void pi_zmq_start (void) {
    context = zmq_ctx_new ();
    socket = zmq_socket (context, ZMQ_PAIR);
    int rc = zmq_bind (socket, "tcp://*:5555");
    assert (rc == 0);
}

svLogic pi_umi_recv(int* got_packet, svBitVecVal* rbuf) {
    // start ZMQ if neeced
    if (!socket) {
        pi_zmq_start();
    }

    // try to receive data
    uint8_t buf[32];
    int nrecv = zmq_recv(socket, buf, 32, ZMQ_NOBLOCK);

    if (nrecv == 32) {
        *got_packet = 1;

        // acknowledge receipt of data
        zmq_send(socket, NULL, 0, 0);

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
    // start ZMQ if neeced
    if (!socket) {
        pi_zmq_start();
    }

    // copy data into a buffer.  we can't directly use sbuf
    // with zmq_send, because it is an array of uint32_t
    uint8_t buf[32];
    for (int i=0; i<32; i++) {
        buf[i] = sbuf[i];
    }

    // send message
    zmq_send(socket, buf, 32, 0);
	zmq_recv(socket, NULL, 0, 0);

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