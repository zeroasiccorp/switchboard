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
static void *rx_socket = NULL;
static void *tx_socket = NULL;
static struct timeval stop_time, start_time;

void pi_umi_init (char *userdata) {
    vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;

    // argument is unused
    (void)userdata;

    // set up mechanism to get arguments
	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);

    // create ZMQ context
    context = zmq_ctx_new ();

    // determine RX URI
    argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
    vpi_get_value(argh, &argval);
    int rx_port = argval.value.integer;
    char rx_uri[128];
    sprintf(rx_uri, "tcp://*:%d", rx_port);

    // set up RX port
    rx_socket = zmq_socket (context, ZMQ_REP);
    int rcrx = zmq_bind (rx_socket, rx_uri);
    assert (rcrx == 0);

    // determine TX URI
    argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
    vpi_get_value(argh, &argval);
    int tx_port = argval.value.integer;
    char tx_uri[128];
    sprintf(tx_uri, "tcp://localhost:%d", tx_port);

    // set up TX port
    tx_socket = zmq_socket (context, ZMQ_REQ);
    int rctx = zmq_connect (tx_socket, tx_uri);
    assert (rctx == 0);

}

void pi_umi_recv(char *userdata) {
    vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;

    // argument is unused
    (void)userdata;

    // make sure that RX socket has started
    assert(rx_socket);

    // try to receive data
    uint8_t rbuf[32];
    int nrecv = zmq_recv(rx_socket, rbuf, 32, ZMQ_NOBLOCK);

    // acknowledge if needed
    int got_packet;
    if (nrecv == 32) {
        zmq_send(rx_socket, NULL, 0, 0);
        got_packet = 1;
    } else {
        got_packet = 0;
    }

    // interface with VPI arguments
	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);
	
    // indicate if a packet was received
    argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
    argval.value.integer = got_packet;
    vpi_put_value(argh, &argval, NULL, vpiNoDelay);

    // write back data that was read
    if (got_packet){
        argh = vpi_scan(args_iter);
        vpiHandle elem;
        for (int i=0; i<32; i++) {
            elem = vpi_handle_by_index(argh, i);
            argval.value.integer = (uint32_t)rbuf[i];
            vpi_put_value(elem, &argval, NULL, vpiNoDelay);
        }
    }

    // cleanup
    vpi_free_object(args_iter);
}

void pi_umi_send(char *userdata) {
    vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;

    // argument is unused
    (void)userdata;

    // make sure that TX socket has started
    assert(tx_socket);

    // interface with VPI arguments
	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);

    // send each item
    argh = vpi_scan(args_iter);
    argval.format = vpiIntVal;
    vpiHandle elem;
    uint8_t sbuf[32];
    for (int i=0; i<32; i=i+1) {
        elem = vpi_handle_by_index(argh, i);
        vpi_get_value(elem, &argval);
        sbuf[i] = (uint8_t)argval.value.integer;
    }

    // send message
    zmq_send(tx_socket, sbuf, 32, 0);
	zmq_recv(tx_socket, NULL, 0, 0);

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

void register_pi_umi_init(void) {
    s_vpi_systf_data data = {
		vpiSysTask,
		0,
		"$pi_umi_init",
		(void *)pi_umi_init,
		0,
		0,
		0
	};

	vpi_register_systf(&data);
}

void register_pi_umi_recv(void) {
    s_vpi_systf_data data = {
		vpiSysTask,
		0,
		"$pi_umi_recv",
		(void *)pi_umi_recv,
		0,
		0,
		0
	};

	vpi_register_systf(&data);
}

void register_pi_umi_send(void) {
    s_vpi_systf_data data = {
		vpiSysTask,
		0,
		"$pi_umi_send",
		(void *)pi_umi_send,
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
	register_pi_umi_init,
    register_pi_umi_recv,
    register_pi_umi_send,
    register_pi_time_taken,
	0  // last entry must be 0
};