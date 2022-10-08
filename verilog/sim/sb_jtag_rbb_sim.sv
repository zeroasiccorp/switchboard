module sb_jtag_rbb_sim (
    input clk,
    input rst,
    output tck,
    output tms,
    output tdi,
    input tdo,
    output trst,
    output srst,
    output reg led=1'b0
);
    // SB DPI/VPI interface

    integer rxid, txid;

	`ifdef __ICARUS__
		task init(input string rxuri, input string txuri);
			$pi_sb_rx_init(rxid, rxuri);
            $pi_sb_rx_init(txid, txuri);
		endtask

		task pi_sb_recv(input int id, output [255:0] rdata, output [31:0] rdest,
			output rlast, output int success);
			$pi_sb_recv(id, rdata, rdest, rlast, success);
		endtask

		task pi_sb_send(input int id, input [255:0] sdata, input [31:0] sdest,
			input slast, output int success);
			$pi_sb_send(id, sdata, sdest, slast, success);
		endtask

		reg [255:0] sdata;
		reg [31:0] sdest;
		reg slast;

		reg [255:0] rdata;
		reg [31:0] rdest;
		reg rlast;
	`else
		import "DPI-C" function void pi_sb_rx_init(output int id, input string uri);
		import "DPI-C" function void pi_sb_recv(input int id, output bit [255:0] rdata,
			output bit [31:0] rdest, output bit rlast, output int success);

		import "DPI-C" function void pi_sb_tx_init (output int id, input string uri);
		import "DPI-C" function void pi_sb_send (input int id, input bit [255:0] sdata, 
			input bit [31:0] sdest, input bit slast, output int success);

		function void init(input string rxuri, input string txuri);
			/* verilator lint_off IGNOREDRETURN */
			pi_sb_rx_init(rxid, rxuri);
            pi_sb_tx_init(txid, txuri);
			/* verilator lint_on IGNOREDRETURN */
		endfunction

		var bit [255:0] rdata;
		var bit [31:0] rdest;
		var bit rlast;

		var bit [255:0] sdata;
		var bit [31:0] sdest;
		var bit slast;
	`endif


    // initialize

    integer r_success;
    integer s_success;

    initial begin
        sdata = 256'd0;
        sdest = 32'd0;
        slast = 1'b1;
    end

    // main logic

    reg [31:0] read_count = 32'd0;

    // convenient to group these together,
    // so that the output value can be computed
    // from the incoming ASCII command

    reg [2:0] tck_tms_tdi = 3'b011;
    assign tck = tck_tms_tdi[2];
    assign tms = tck_tms_tdi[1];
    assign tdi = tck_tms_tdi[0];

    reg [1:0] trst_srst = 2'b11;
    assign trst = trst_srst[1];
    assign srst = trst_srst[0];

    always @(posedge clk) begin
        if (rst) begin
            // external pins
            tck_tms_tdi <= 3'b011;
            trst_srst <= 2'b11;
            led <= 1'b0;

            // internal state
            read_count <= 32'd0;
        end else begin
            // write output value
            if (read_count > 0) begin
                sdata[7:0] = tdo ? "1" : "0";
                pi_sb_send(txid, sdata, sdest, slast, s_success);
                if (s_success == 32'd1) begin
                    read_count <= read_count - 1;
                end
            end

            // get next command as long as long as it
            // couldn't overflow the read counter
            if (read_count < 32'h7fffffff) begin
                pi_sb_recv(rxid, rdata, rdest, rlast, r_success);
                if (r_success == 32'd1) begin
                    if (rdata[7:0] == "B") begin
                        led <= 1'b1;
                    end else if (rdata[7:0] == "b") begin
                        led <= 1'b0;
                    end else if (rdata[7:0] == "R") begin
                        read_count <= read_count + 32'd1;
                    end else if (rdata[7:0] == "Q") begin
                        // TODO: quit
                    end else if (("0" <= rdata[7:0]) && (rdata[7:0] <= "7")) begin
                        /* verilator lint_off WIDTH */
                        tck_tms_tdi <= {rdata[7:0] - "0"};
                        /* verilator lint_on WIDTH */
                    end else if (("r" <= rdata[7:0]) && (rdata[7:0] <= "u")) begin
                        /* verilator lint_off WIDTH */
                        trst_srst <= {rdata[7:0] - "r"};
                        /* verilator lint_on WIDTH */
                    end
                end
            end
        end
    end
endmodule
