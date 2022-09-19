module testbench (
	input clk
);
	// UMI RX port

	wire [255:0] umi_packet_rx;
	wire umi_valid;
	wire umi_ready;

	// UMI TX port

	wire [255:0] umi_packet_tx;
	wire umi_valid;
	wire umi_ready;

	umi_rx_sim rx_i (
		.clk(clk),
		.ready(umi_ready), // input
		.packet(umi_packet_rx), // output
		.valid(umi_valid) // output
	);

	umi_tx_sim tx_i (
		.clk(clk),
		.ready(umi_ready), // output
		.packet(umi_packet_tx), // input
		.valid(umi_valid) // input
	);

	// custom modification of packet

	genvar i;
	generate
		for (i=0; i<8; i=i+1) begin
			assign umi_packet_tx[(i*32) +: 32] = umi_packet_rx[(i*32) +: 32] + 32'd1;
		end
	endgenerate

	string rx_port;	
	string tx_port;

	initial begin
		// read command-line arguments, setting defaults as needed
		
		if (!$value$plusargs("rx_port=%s", rx_port)) begin
			rx_port = "queue-5555";
		end		
		
		if (!$value$plusargs("tx_port=%s", tx_port)) begin
			tx_port = "queue-5556";
		end
		
		// initialize UMI according to command-line arguments

		/* verilator lint_off IGNOREDRETURN */
		rx_i.init(rx_port);
		tx_i.init(tx_port);
		/* verilator lint_on IGNOREDRETURN */
	end

endmodule
