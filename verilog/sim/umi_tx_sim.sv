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

		task pi_umi_send(input int id, input [31:0] sbuf [0:7], output int success);
			$pi_umi_send(id, sbuf, success);
		endtask

		wire [31:0] sbuf [0:7];
	`else
		import "DPI-C" function pi_umi_init (output int id, input string uri, input int is_tx);
		import "DPI-C" function pi_umi_send (input int id, input bit [31:0] sbuf [0:7], output int success);

		function init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			pi_umi_init(id, uri, 0);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		wire bit [31:0] sbuf [0:7];
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

	genvar i;
	generate
		for (i=0; i<8; i=i+1) begin
			assign sbuf[i] = packet[(((i+1)*32)-1):(i*32)];
		end
	endgenerate

endmodule
