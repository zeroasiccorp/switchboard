module umi_rx_sim (
	input clk,
	input ready,
	output [255:0] packet,
	output valid
);
	// internal signals

	integer id;
	integer success;
	reg in_progress = 1'b0;
	reg valid_reg = 1'b0;

	// handle differences between simulators

	`ifdef __ICARUS__
		task init(input string uri);
			$pi_umi_init(id, uri, 0);
		endtask

		task pi_umi_recv(input int id, output [31:0] rbuf [0:7], output int success);
			$pi_umi_recv(id, rbuf, success);
		endtask

		reg [31:0] rbuf [0:7];
	`else
		import "DPI-C" function pi_umi_init(output int id, input string uri, input int is_tx);
		import "DPI-C" function pi_umi_recv(input int id, output bit [31:0] rbuf [0:7], output int success);

		function init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			pi_umi_init(id, uri, 0);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		var bit [31:0] rbuf [0:7];
	`endif

	// main logic

    always @(posedge clk) begin
    	if (in_progress) begin
			if (ready) begin
				valid_reg <= 1'b0;
				in_progress <= 1'b0;
            end
		end else begin
			/* verilator lint_off IGNOREDRETURN */
			pi_umi_recv(id, rbuf, success);
			/* verilator lint_on IGNOREDRETURN */
			if (success == 32'd1) begin
				valid_reg <= 1'b1;
				in_progress <= 1'b1;
			end
		end
    end

	// wire up I/O

	assign valid = valid_reg;

	genvar i;
	generate
		for (i=0; i<8; i=i+1) begin
			assign packet[(((i+1)*32)-1):(i*32)] = rbuf[i];
		end
	endgenerate

endmodule