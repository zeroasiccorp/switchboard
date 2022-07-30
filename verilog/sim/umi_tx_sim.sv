module umi_tx_sim (
	input clk,
	input valid,
	input [255:0] packet,
	output ready
);
	// internal signals

	integer id;
	integer success;
	reg in_progress = 1'b0;
	reg ready_reg;

	// handle differences between simulators

	`ifdef __ICARUS__
		task init(input string uri);
			$pi_umi_init(id, uri, 0);
		endtask

		task pi_umi_send(input int id, input [255:0] sbuf, output int success);
			$pi_umi_send(id, sbuf, success);
		endtask

		wire [255:0] sbuf;
	`else
		import "DPI-C" function void pi_umi_init (output int id, input string uri, input int is_tx);
		import "DPI-C" function void pi_umi_send (input int id, input bit [255:0] sbuf, output int success);

		function void init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			pi_umi_init(id, uri, 0);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		// TODO: is this variable really necessary?  perhaps it is optimized
		// away by verilator, but if not, it might be worth removing, since
		// its only purpose is to convert the type of the packet signal from
		// "logic" (default) to "bit".  in Verilator, all signals are 2-level
		// anyway, so this should have no effect...
		wire bit [255:0] sbuf;
	`endif

    // main logic

	always @(posedge clk) begin
		if (in_progress) begin
			ready_reg <= 1'b0;
			in_progress <= 1'b0;
		end else begin
			if (valid) begin
				/* verilator lint_off IGNOREDRETURN */
				pi_umi_send(id, sbuf, success);
				/* verilator lint_on IGNOREDRETURN */
				if (success == 32'd1) begin
					ready_reg <= 1'b1;
					in_progress <= 1'b1;
				end
			end
		end
	end

	// wire up I/O

	assign ready = ready_reg;
	assign sbuf = packet;

endmodule
