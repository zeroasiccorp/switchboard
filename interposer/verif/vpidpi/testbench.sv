`timescale 1ns/1ps

`ifdef DPI
	`define PI(f) ``f``
	`define VAR_BIT var bit
	`define WIRE_BIT wire bit
`else
	`define PI(f) $``f``
	`define VAR_BIT reg
	`define WIRE_BIT wire
`endif

module testbench(
	`ifdef VERILATOR
		input clk
	`endif
);
    // clock
	`ifndef VERILATOR
		reg clk = 1'b0;
		always begin
			clk = 1'b0;
			#5;
			clk = 1'b1;
			#5;
    	end
	`endif

	// DPI imports
	`ifdef DPI
		import "DPI-C" function pi_zmq_recv (output int nrecv, output bit [7:0] rbuf [0:31]);
		import "DPI-C" function pi_zmq_send (input int nsend, input bit [7:0] sbuf [0:31]);
		import "DPI-C" function pi_time_taken (output real t);
	`endif

	// UMI RX port
	wire [255:0] umi_packet_rx;
	reg umi_valid_rx = 1'b0;
	wire umi_ready_rx;

	// UMI TX port
	wire [255:0] umi_packet_tx;
	wire umi_valid_tx;
	reg umi_ready_tx = 1'b0;

    // instantiate top-level module
    zverif_top zverif_top_i (
	    .clk(clk),
	    .trap(),
	    .trace_valid(),
	    .trace_data(),
        .umi_packet_rx(umi_packet_rx),
	    .umi_valid_rx(umi_valid_rx),
	    .umi_ready_rx(umi_ready_rx),
	    .umi_packet_tx(umi_packet_tx),
	    .umi_valid_tx(umi_valid_tx),
	    .umi_ready_tx(umi_ready_tx)
    );

    // UMI RX

    integer nrecv;
	integer zmq_counter = 0;
	`VAR_BIT [7:0] rbuf [0:31];
    reg rx_in_progress = 1'b0;
    always @(posedge clk) begin
    	if (rx_in_progress) begin
			if (umi_ready_rx) begin
				umi_valid_rx <= 1'b0;
				rx_in_progress <= 1'b0;
            end 
		end else begin
			if (zmq_counter == `CYCLES_PER_RECV) begin
				/* verilator lint_off IGNOREDRETURN */
				`PI(pi_zmq_recv)(nrecv, rbuf);
				/* verilator lint_on IGNOREDRETURN */
				umi_valid_rx <= 1'b1;
				rx_in_progress <= 1'b1;
				zmq_counter <= 0;
			end else begin
				zmq_counter <= zmq_counter + 1;
			end
		end
    end

    // UMI TX

	`WIRE_BIT [7:0] sbuf [0:31];
	reg tx_in_progress = 1'b0;
	always @(posedge clk) begin
		if (tx_in_progress) begin
			umi_ready_tx <= 1'b0;
			tx_in_progress <= 1'b0;
		end else begin
			if (umi_valid_tx) begin
				/* verilator lint_off IGNOREDRETURN */
				`PI(pi_zmq_send)(32, sbuf);
				/* verilator lint_on IGNOREDRETURN */
				umi_ready_tx <= 1'b1;
				tx_in_progress <= 1'b1;
			end
		end
	end

	// wire up rbuf and sbuf
	genvar i;
	generate
		for (i=0; i<32; i=i+1) begin
			assign umi_packet_rx[(((i+1)*8)-1):(i*8)] = rbuf[i];
			assign sbuf[i] = umi_packet_tx[(((i+1)*8)-1):(i*8)];
		end
	endgenerate

	// performance measurement
	integer total_clock_cycles = 0;
	real t, sim_rate;
	initial begin
		/* verilator lint_off IGNOREDRETURN */
		`PI(pi_time_taken)(t);
		/* verilator lint_on IGNOREDRETURN */
	end
	always @(posedge clk) begin
		if (total_clock_cycles >= `CYCLES_PER_MEAS) begin
			/* verilator lint_off IGNOREDRETURN */
			`PI(pi_time_taken)(t);
			/* verilator lint_on IGNOREDRETURN */
			sim_rate = (1.0*total_clock_cycles)/t;
			if (sim_rate < 1.0e6) begin
				$display("Simulation rate: %0.3f kHz", 1e-3*sim_rate);
			end else begin
				$display("Simulation rate: %0.3f MHz", 1e-6*sim_rate);
			end
			total_clock_cycles <= 0;
		end else begin
			total_clock_cycles <= total_clock_cycles + 1;
		end
	end

endmodule