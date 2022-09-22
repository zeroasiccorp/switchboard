module testbench (
	input clk
);
	// UMI RX port

	wire [255:0] umi_rx_packet;
	wire umi_rx_valid;
	wire umi_rx_ready;

	// UMI TX port

	wire [255:0] umi_tx_packet;
	wire umi_tx_valid;
	wire umi_tx_ready;

	umi_rx_sim rx_i (
		.clk(clk),
		.packet(umi_rx_packet), // output
		.ready(umi_rx_ready), // input
		.valid(umi_rx_valid) // output
	);

	umi_tx_sim tx_i (
		.clk(clk),
		.packet(umi_tx_packet), // input
		.ready(umi_tx_ready), // output
		.valid(umi_tx_valid) // input
	);

	// instantiate module with UMI ports

	umiram ram_i (
		.*
	);


	// Initialize UMI

	initial begin
		/* verilator lint_off IGNOREDRETURN */
		rx_i.init($sformatf("queue-%0d", 5555));
		tx_i.init($sformatf("queue-%0d", 5556));
		/* verilator lint_on IGNOREDRETURN */
	end

endmodule
