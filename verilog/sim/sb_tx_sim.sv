module sb_tx_sim (
	input clk,
	input [255:0] data,
	input [31:0] dest,
	input last,
	output ready,
	input valid
);
	// internal signals

	integer id;
	integer success;
	reg in_progress = 1'b0;
	reg ready_reg;

	// handle differences between simulators

	`ifdef __ICARUS__
		task init(input string uri);
			$pi_sb_tx_init(id, uri);
		endtask

		task pi_sb_send(input int id, input [255:0] sdata, input [31:0] sdest,
			input slast, output int success);
			$pi_sb_send(id, sdata, sdest, slast, success);
		endtask

		wire [255:0] sdata;
		wire [31:0] sdest;
		wire slast;
	`else
		import "DPI-C" function void pi_sb_tx_init (output int id, input string uri);
		import "DPI-C" function void pi_sb_send (input int id, input bit [255:0] sdata, 
			input bit [31:0] sdest, input bit slast, output int success);

		function void init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			pi_sb_tx_init(id, uri);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		// TODO: is this variable really necessary?  perhaps it is optimized
		// away by verilator, but if not, it might be worth removing, since
		// its only purpose is to convert the type of the packet signal from
		// "logic" (default) to "bit".  in Verilator, all signals are 2-level
		// anyway, so this should have no effect...
		wire bit [255:0] sdata;
		wire bit [31:0] sdest;
		wire bit slast;
	`endif

    // main logic

	always @(posedge clk) begin
		if (in_progress) begin
			ready_reg <= 1'b0;
			in_progress <= 1'b0;
		end else begin
			if (valid) begin
				/* verilator lint_off IGNOREDRETURN */
				pi_sb_send(id, sdata, sdest, slast, success);
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
	assign sdata = data;
	assign sdest = dest;
	assign slast = last;

endmodule
