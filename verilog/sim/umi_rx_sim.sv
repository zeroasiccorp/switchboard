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

		task pi_umi_recv(input int id, output [255:0] rbuf, output int success);
			$pi_umi_recv(id, rbuf, success);
		endtask

		reg [255:0] rbuf;
	`else
		import "DPI-C" function void pi_umi_init(output int id, input string uri, input int is_tx);
		import "DPI-C" function void pi_umi_recv(input int id, output bit [255:0] rbuf, output int success);

		function void init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			pi_umi_init(id, uri, 0);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		var bit [255:0] rbuf;
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
	assign packet = rbuf;

endmodule