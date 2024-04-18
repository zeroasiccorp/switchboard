// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

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
    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
        `define SB_VAR_BIT reg
    `else
        `define SB_EXT_FUNC(x) x
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
        `define SB_VAR_BIT var bit

        import "DPI-C" function void pi_sb_rx_init(output int id, input string uri);
        import "DPI-C" function void pi_sb_recv(input int id, output bit [255:0] rdata,
            output bit [31:0] rdest, output bit rlast, output int success);

        import "DPI-C" function void pi_sb_tx_init (output int id, input string uri);
        import "DPI-C" function void pi_sb_send (input int id, input bit [255:0] sdata,
            input bit [31:0] sdest, input bit slast, output int success);
    `endif

    // SB DPI/VPI interface

    integer rxid=-1;
    integer txid=-1;

    `SB_START_FUNC init(input string rxuri, input string txuri);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_rx_init)(rxid, rxuri);
        `SB_EXT_FUNC(pi_sb_tx_init)(txid, txuri);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_VAR_BIT [255:0] sdata;
    `SB_VAR_BIT [31:0] sdest;
    `SB_VAR_BIT slast;

    `SB_VAR_BIT [255:0] rdata;
    `SB_VAR_BIT [31:0] rdest;
    `SB_VAR_BIT rlast;

    // initialize

    integer r_success = 0;
    integer s_success = 0;

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
                sdata[7:0] = tdo ? "1" : "0";  // intended to be blocking
                if (txid != -1) begin
                    `SB_EXT_FUNC(pi_sb_send)(txid, sdata, sdest, slast, s_success);
                end else begin
                    s_success = 32'd0;
                end
                if (s_success == 32'd1) begin
                    read_count <= read_count - 1;
                end
            end

            // get next command as long as long as it
            // couldn't overflow the read counter
            if (read_count < 32'h7fffffff) begin
                if (rxid != -1) begin
                    `SB_EXT_FUNC(pi_sb_recv)(rxid, rdata, rdest, rlast, r_success);
                end else begin
                    r_success = 32'd0;
                end
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

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_START_FUNC
    `undef SB_END_FUNC
    `undef SB_VAR_BIT

endmodule

`default_nettype wire
