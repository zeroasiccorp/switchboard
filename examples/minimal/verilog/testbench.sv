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

	// Initialize UMI

	initial begin
		/* verilator lint_off IGNOREDRETURN */
		rx_i.init($sformatf("queue-%0d", 5555));
		tx_i.init($sformatf("queue-%0d", 5556));
		/* verilator lint_on IGNOREDRETURN */
	end

endmodule
