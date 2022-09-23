module sb_rx_sim (
	input clk,
	output [255:0] data,
	output [31:0] dest,
	output last,
	input ready,
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
			$pi_sb_rx_init(id, uri);
		endtask

		task pi_sb_recv(input int id, output [255:0] rdata, output [31:0] rdest,
			output rlast, output int success);
			$pi_sb_recv(id, rbuf, rdest, rlast, success);
		endtask

		reg [255:0] rdata;
		reg [31:0] rdest;
		reg rlast;
	`else
		import "DPI-C" function void pi_sb_rx_init(output int id, input string uri);
		import "DPI-C" function void pi_sb_recv(input int id, output bit [255:0] rdata,
			output bit [31:0] rdest, output bit rlast, output int success);

		function void init(input string uri);
			/* verilator lint_off IGNOREDRETURN */
			pi_sb_rx_init(id, uri);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		var bit [255:0] rdata;
		var bit [31:0] rdest;
		var bit rlast;
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
			pi_sb_recv(id, rdata, rdest, rlast, success);
			/* verilator lint_on IGNOREDRETURN */
			if (success == 32'd1) begin
				valid_reg <= 1'b1;
				in_progress <= 1'b1;
			end
		end
    end

	// wire up I/O

	assign data = rdata;
	assign dest = rdest;
	assign last = rlast;
	assign valid = valid_reg;

endmodule
