#include <sys/time.h>

// ZMQ stuff
#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>

// VPI stuff
#include <vpi_user.h>

static void *context = NULL;
static void *socket = NULL;
static struct timeval stop_time, start_time;

void pi_zmq_start (void) {
    context = zmq_ctx_new ();
    socket = zmq_socket (context, ZMQ_PAIR);
    int rc = zmq_bind (socket, "tcp://*:5555");
    assert (rc == 0);
}

void pi_zmq_recv(char *userdata) {
    vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;

    // argument is unused
    (void)userdata;

    // start ZMQ if neeced
    if (!socket) {
        pi_zmq_start();
    }

    // try to receive data
    uint8_t rbuf[32];
    int nrecv = zmq_recv(socket, rbuf, 32, ZMQ_NOBLOCK);

    // acknowledge if needed
    if (nrecv == 32) {
        zmq_send(socket, NULL, 0, 0);
    }

    // interface with VPI arguments
	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);
	
    // write back number of items read
    argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
    argval.value.integer = nrecv;
    vpi_put_value(argh, &argval, NULL, vpiNoDelay);

    // write back data that was read
    if (nrecv == 32){
        argh = vpi_scan(args_iter);
        vpiHandle elem;
        for (int i=0; i<nrecv; i++) {
            elem = vpi_handle_by_index(argh, i);
            argval.value.integer = (uint32_t)rbuf[i];
            vpi_put_value(elem, &argval, NULL, vpiNoDelay);
        }
    }

    // cleanup
    vpi_free_object(args_iter);
}

void pi_zmq_send(char *userdata) {
    vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;

    // argument is unused
    (void)userdata;

    // start ZMQ if neeced
    if (!socket) {
        pi_zmq_start();
    }

    // interface with VPI arguments
	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);
	
    // get number of items to write
	argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
	vpi_get_value(argh, &argval);
	int nsend = argval.value.integer;

    // send each items
    argh = vpi_scan(args_iter);
    vpiHandle elem;
    uint8_t sbuf[32];
    for (int i=0; i<nsend; i=i+1) {
        elem = vpi_handle_by_index(argh, i);
        vpi_get_value(elem, &argval);
        sbuf[i] = (uint8_t)argval.value.integer;
    }

    // send message
    zmq_send(socket, sbuf, nsend, 0);
	zmq_recv(socket, NULL, 0, 0);

	// Cleanup and return
	vpi_free_object(args_iter);
}

void pi_time_taken(char *userdata) {
    vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;

    // argument is unused
    (void)userdata;

    // get the time taken
    double time_taken;
    unsigned long time_taken_us = 0;
	gettimeofday(&stop_time, NULL);
    time_taken_us += ((stop_time.tv_sec - start_time.tv_sec) * 1000000);
    time_taken_us += (stop_time.tv_usec - start_time.tv_usec);
    time_taken = 1.0e-6*time_taken_us;
    gettimeofday(&start_time, NULL);

    // interface with VPI arguments
	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);
	
    // write back number of items read
    argh = vpi_scan(args_iter);
	argval.format = vpiRealVal;
    argval.value.real = time_taken;
    vpi_put_value(argh, &argval, NULL, vpiNoDelay);

	// Cleanup and return
	vpi_free_object(args_iter);
}

void register_pi_zmq_recv(void) {
    s_vpi_systf_data data = {
		vpiSysTask,
		0,
		"$pi_zmq_recv",
		(void *)pi_zmq_recv,
		0,
		0,
		0
	};

	vpi_register_systf(&data);
}

void register_pi_zmq_send(void) {
    s_vpi_systf_data data = {
		vpiSysTask,
		0,
		"$pi_zmq_send",
		(void *)pi_zmq_send,
		0,
		0,
		0
	};

	vpi_register_systf(&data);
}

void register_pi_time_taken(void) {
    s_vpi_systf_data data = {
		vpiSysTask,
		0,
		"$pi_time_taken",
		(void *)pi_time_taken,
		0,
		0,
		0
	};

	vpi_register_systf(&data);
}

void (*vlog_startup_routines[])(void) = {
	register_pi_zmq_recv,
    register_pi_zmq_send,
    register_pi_time_taken,
	0  // last entry must be 0
};