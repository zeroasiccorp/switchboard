module testbench (
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

	// UMI RX port
	wire [255:0] umi_packet_rx;
	reg umi_valid_rx = 1'b0;
	wire umi_ready_rx;

	// UMI TX port
	wire [255:0] umi_packet_tx;
	wire umi_valid_tx;
	reg umi_ready_tx = 1'b0;

    // instantiate top-level module
    dut dut_i (
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

	umi_rx_sim rx_i (
		.clk(clk),
		.ready(umi_ready_rx),
		.packet(umi_packet_rx),
		.valid(umi_valid_rx)
	);


	umi_tx_sim tx_i (
		.clk(clk),
		.ready(umi_ready_tx),
		.packet(umi_packet_tx),
		.valid(umi_valid_tx)
	);

	// Initialize UMI
	integer rx_port;
	integer tx_port;
	initial begin
		// read command-line arguments, setting defaults as needed
		if (!$value$plusargs("rx_port=%d", rx_port)) begin
			rx_port = 5555;
		end
		if (!$value$plusargs("tx_port=%d", tx_port)) begin
			tx_port = 5556;
		end

		/* verilator lint_off IGNOREDRETURN */
		rx_i.init($sformatf("queue-%0d", rx_port));
		tx_i.init($sformatf("queue-%0d", tx_port));
		/* verilator lint_on IGNOREDRETURN */
	end

endmodule