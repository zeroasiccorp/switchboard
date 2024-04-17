// queue_to_sb_sim

// valid_mode settings (in all cases, valid remains low if there is no incoming data)
// valid_mode=0: valid alternates between "0" and "1" if there is a continuous stream of incoming data
// valid_mode=1: valid remains at "1" if there is a continuous stream of incoming data
// valid_mode=2: valid toggles randomly if there is a continuous stream of incoming data

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module queue_to_sb_sim #(
    parameter integer VALID_MODE_DEFAULT=0,
    parameter integer DW=416,
    parameter FILE=""
) (
    input clk,
    output [DW-1:0] data,
    output reg [31:0] dest=32'b0,
    output reg last=1'b0,
    input ready,
    output reg valid=1'b0
);
    // SBDW value corresponds to UMI DW=256
    // 32b (cmd) + 64b (srcaddr) + 64b (dstaddr) + 256b = 416b

    // SBDW must be a multiple of 32 (constrained by VPI driver,
    // which transfers data in 32-bit chunks)
    localparam SBDW = 416;

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

        import "DPI-C" function void pi_sb_rx_init(output int id,
            input string uri, input int width);
        import "DPI-C" function void pi_sb_recv(input int id, output bit [SBDW-1:0] rdata,
            output bit [31:0] rdest, output bit rlast, output int success);
    `endif

    // internal signals

    integer id = -1;

    `SB_START_FUNC init(input string uri);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_rx_init)(id, uri, (DW + 7)/8);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    integer success = 0;

    `SB_VAR_BIT [SBDW-1:0] rdata;
    `SB_VAR_BIT [31:0] rdest;
    `SB_VAR_BIT rlast;

    `SB_VAR_BIT [SBDW-1:0] data_padded = 'b0;
    assign data = data_padded[DW-1:0];

    initial begin
        rdata = 'b0;
        rdest = 32'b0;
        rlast = 1'b0;
    end

    // valid mode

    integer valid_mode = VALID_MODE_DEFAULT;

    `SB_START_FUNC set_valid_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        valid_mode = value;
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // main logic

    always @(posedge clk) begin
        if (ready && valid) begin
            // the transaction has completed, so we can try to get another
            // packet if we want to.  whether we try to do this or not depends
            // on the valid_mode setting.

            if ((valid_mode == 32'd1) ||
                ((valid_mode == 32'd2) && ($random % 2 == 32'd1))) begin
                // try to receive a packet
                if (id != -1) begin
                    /* verilator lint_off IGNOREDRETURN */
                    `SB_EXT_FUNC(pi_sb_recv)(id, rdata, rdest, rlast, success);
                    /* verilator lint_on IGNOREDRETURN */
                end else begin
                    /* verilator lint_off BLKSEQ */
                    success = 32'd0;
                    /* verilator lint_on BLKSEQ */
                end

                // if a packet was received, mark the output as valid
                if (success == 32'd0) begin
                    valid <= 1'b0;
                end else begin
                    valid <= 1'b1;
                    data_padded <= rdata;
                    dest <= rdest;
                    last <= rlast;
                end
            end else begin
                valid <= 1'b0;
            end
        end else if (!valid) begin
            // if there isn't a packet being presented, we can try to get one
            // to present.  whether we do or not depends on valid_mode: if
            // valid_mode=2, then flip a coin to decide if a new packet is read.
            // in any other case, try to read a packet.

            if ((valid_mode == 32'd0) || (valid_mode == 32'd1) ||
                ((valid_mode == 32'd2) && ($random % 2 == 32'd1))) begin
                // try to receive a packet
                if (id != -1) begin
                    /* verilator lint_off IGNOREDRETURN */
                    `SB_EXT_FUNC(pi_sb_recv)(id, rdata, rdest, rlast, success);
                    /* verilator lint_on IGNOREDRETURN */
                end else begin
                    /* verilator lint_off BLKSEQ */
                    success = 32'd0;
                    /* verilator lint_on BLKSEQ */
                end

                // if a packet was received, mark the output as valid
                if (success == 32'd0) begin
                    valid <= 1'b0;
                end else begin
                    valid <= 1'b1;
                    data_padded <= rdata;
                    dest <= rdest;
                    last <= rlast;
                end
            end else begin
                valid <= 1'b0;
            end
        end
    end

    // initialize

    initial begin
        if (FILE != "") begin
            /* verilator lint_off IGNOREDRETURN */
            init(FILE);
            /* verilator lint_on IGNOREDRETURN */
        end
    end

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_START_FUNC
    `undef SB_END_FUNC
    `undef SB_VAR_BIT

endmodule

`default_nettype wire
