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

	// AXI signals for writing to RAM or GPIO
	bool write_in_progress = false;
	uint8_t ext_awvalid=0, ext_wvalid=0, ext_bready=0;
	uint32_t ext_awaddr=0, ext_wdata=0;

	// AXI signals for receiving transactions from the processor
	uint8_t ctrl_awready=0, ctrl_wready=0, ctrl_bvalid=0;

	int cyc_count = 0;

	while (!Verilated::gotFinish()) {
		// determine next value of outputs when clock is about
		// to go high (i.e., when it currently reads low).  these
		// outputs are driven right after the clock edge
		if (!top->clk) {
			// write data to the device
			if (write_in_progress) {
				if (top->ext_awready) {
					ext_awvalid = 0;
				}
				if (top->ext_wready) {
					ext_wvalid = 0;
				}
				if (top->ext_bvalid) {
					ext_bready = 1;
					write_in_progress = false;
				}		
			} else {
				if (cyc_count == 1000){
					// only try to receive data occasionally, since this becomes the
					// bottleneck for simulation
					int nrecv;
					uint8_t rbuf[8];
					if ((nrecv = zmq_recv (socket, rbuf, 8, ZMQ_NOBLOCK)) == 8) {
						zmq_send(socket, NULL, 0, 0);  // ACK
						ext_awaddr = (rbuf[7] << 24) | (rbuf[6] << 16) | (rbuf[5] << 8) | rbuf[4];
						ext_wdata = (rbuf[3] << 24) | (rbuf[2] << 16) | (rbuf[1] << 8) | rbuf[0];
						ext_awvalid = 1;
						ext_wvalid = 1;
						ext_bready = 0;
						write_in_progress = true;
					}
					cyc_count = 0;
				} else {
					cyc_count += 1;
				}
			}

			// look for writes
			if (top->ctrl_awvalid && top->ctrl_wvalid &&
				((!top->ctrl_awready) && (!top->ctrl_wready)) &&
				((!top->ctrl_bvalid) || top->ctrl_bready)) {
				uint8_t sbuf[8];
				sbuf[7] = (top->ctrl_awaddr >> 24) & 0xff;
				sbuf[6] = (top->ctrl_awaddr >> 16) & 0xff;
				sbuf[5] = (top->ctrl_awaddr >> 8) & 0xff;
				sbuf[4] = (top->ctrl_awaddr >> 0) & 0xff;
				sbuf[3] = (top->ctrl_wdata >> 24) & 0xff;
				sbuf[2] = (top->ctrl_wdata >> 16) & 0xff;
				sbuf[1] = (top->ctrl_wdata >> 8) & 0xff;
				sbuf[0] = (top->ctrl_wdata >> 0) & 0xff;
				zmq_send(socket, sbuf, 8, 0);
				zmq_recv(socket, NULL, 0, 0);

				// handshaking
				ctrl_awready = 1;
				ctrl_wready = 1;
				ctrl_bvalid = 1;
			} else {
				ctrl_awready = 0;
				ctrl_wready = 0;
				ctrl_bvalid = top->ctrl_bvalid && (!top->ctrl_bready);
			}
		}

		// generate clock edge
		top->clk = !top->clk;
		top->eval();

		// drive new outputs
		if (top->clk) {
			top->ext_awvalid = ext_awvalid;
			top->ext_wvalid = ext_wvalid;
			top->ext_bready = ext_bready;
			top->ext_awaddr = ext_awaddr;
			top->ext_wdata = ext_wdata;
			top->ctrl_awready = ctrl_awready;
			top->ctrl_wready = ctrl_wready;
			top->ctrl_bvalid = ctrl_bvalid;
			top->eval();
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

