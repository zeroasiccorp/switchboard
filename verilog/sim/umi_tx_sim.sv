module umi_tx_sim (
	input clk,
	input [255:0] packet,
	output ready,
	input valid
);

	// TODO: support burst mode (through "last")

	sb_tx_sim tx_i (
		.clk(clk),
		.data(packet),
		.dest({16'h0000, packet[255:240]}),
		.last(1'b1),
		.ready(ready),
		.valid(valid)
	);

	// handle differences between simulators

	`ifdef __ICARUS__
		task init(input string uri);
			tx_i.init(uri);
		endtask
	`else
		function void init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			tx_i.init(uri);
			/* verilator lint_on IGNOREDRETURN */
		endfunction
	`endif

endmodule
