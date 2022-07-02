#include <sys/time.h>

// ZMQ stuff
#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>

// Verilator stuff
#include "Vzverif_top.h"
#include "verilated_vcd_c.h"
#include <inttypes.h>

#define CYCLES_PER_RECV 1000

enum state {AXI_RST, PGM_CPU, RUN_CPU};

int main(int argc, char **argv, char **env)
{
	// Start up ZMQ server
    void *context = zmq_ctx_new ();
    void *socket = zmq_socket (context, ZMQ_PAIR);
    int rc = zmq_bind (socket, "tcp://*:5555");
    assert (rc == 0);

	// Instantiate design
	Verilated::commandArgs(argc, argv);
	Vzverif_top* top = new Vzverif_top;

	// Set up optional tracing
	int t = 0;
	VerilatedVcdC* tfp = NULL;
	// Verilated::traceEverOn(true);
	// tfp = new VerilatedVcdC;
	// top->trace (tfp, 99);
	// tfp->open("testbench.vcd");

	bool tx_in_progress = false;
	bool rx_in_progress = false;
	uint8_t clk = 0;
	uint32_t umi_packet_rx [8] = {0};
	uint8_t umi_valid_rx = 0;
	uint8_t umi_ready_tx = 0;

	top->clk = clk;
	for (int i=0; i<8; i++){
		top->umi_packet_rx[i] = umi_packet_rx[i];
	}
	top->umi_valid_rx = umi_valid_rx;
	top->umi_ready_tx = umi_ready_tx;

	top->eval();

	int zmq_counter = 0;

	// performance measurement
	int total_clock_cycles;
	struct timeval stop_time, start_time;
	gettimeofday(&start_time, NULL);

	total_clock_cycles = 0;

	while (!Verilated::gotFinish()) {
		// determine next value of outputs when clock is about
		// to go high (i.e., when it currently reads low).  these
		// outputs are driven right after the clock edge
		if (!clk) {
			// write data to the device
			if (rx_in_progress) {
				if (top->umi_ready_rx) {
					umi_valid_rx = 0;
					rx_in_progress = false;
				}
			} else {
				// only try to receive data occasionally, since this becomes the
				// bottleneck for simulation.  attempting to receive on every
				// clock cycle reduced performance from ~3 MHz to 50 kHz.
				if (zmq_counter == CYCLES_PER_RECV){
					int nrecv;
					uint8_t rbuf[32];
					if ((nrecv = zmq_recv(socket, rbuf, 32, ZMQ_NOBLOCK)) == 32) {
						zmq_send(socket, NULL, 0, 0);  // ACK
						for (int i=0; i<8; i++) {
							umi_packet_rx[i] = 0;
							for (int j=0; j<4; j++) {
								umi_packet_rx[i] |= ((uint32_t)rbuf[(i*4)+j]) << (8*j);
							}
						}
						umi_valid_rx = 1;
						rx_in_progress = true;
					}
					zmq_counter = 0;
				} else {
					zmq_counter += 1;
				}
			}

			// look for writes
			if (tx_in_progress) {
				umi_ready_tx = 0;
				tx_in_progress = false;
			} else {
				if (top->umi_valid_tx) {
					// construct outgoing packet
					uint8_t sbuf[32] = {0};

					// address part
					sbuf[7]  = (top->umi_packet_tx[1] >> 24) & 0xff;
					sbuf[6]  = (top->umi_packet_tx[1] >> 16) & 0xff;
					sbuf[5]  = (top->umi_packet_tx[1] >>  8) & 0xff;
					sbuf[4]  = (top->umi_packet_tx[1] >>  0) & 0xff;

					// data part
					sbuf[15] = (top->umi_packet_tx[3] >> 24) & 0xff;
					sbuf[14] = (top->umi_packet_tx[3] >> 16) & 0xff;
					sbuf[13] = (top->umi_packet_tx[3] >>  8) & 0xff;
					sbuf[12] = (top->umi_packet_tx[3] >>  0) & 0xff;

					// zmq transaction
					zmq_send(socket, sbuf, 32, 0);
					zmq_recv(socket, NULL, 0, 0);

					// handshaking
					umi_ready_tx = 1;
					tx_in_progress = true;
				}
			}
		}

		// generate clock edge
		clk = !clk;
		top->clk = clk;
		top->eval();

		// drive new outputs
		if (clk) {
			for (int i=0; i<8; i++){
				top->umi_packet_rx[i] = umi_packet_rx[i];
			}
			top->umi_valid_rx = umi_valid_rx;
			top->umi_ready_tx = umi_ready_tx;
			top->eval();
		}

		// keep track of performance
		if (clk) {
			total_clock_cycles++;
			if (total_clock_cycles >= 10000000) {
				gettimeofday(&stop_time, NULL);

				unsigned long time_taken_us = 0;
				time_taken_us += ((stop_time.tv_sec - start_time.tv_sec) * 1000000);
				time_taken_us += (stop_time.tv_usec - start_time.tv_usec);
				double sim_rate = total_clock_cycles/(1.0e-6*time_taken_us);
				printf("Simulation rate: %0.3f MHz\n", 1e-6*sim_rate);

				gettimeofday(&start_time, NULL);
				total_clock_cycles = 0;
			}
		}

		// dump waveforms
		if (tfp) {
			tfp->dump(t);
		}

		t += 5;
	}

	// cleanup
	if (tfp) {
		tfp->close();
	}
	delete top;

	return 0;
}
