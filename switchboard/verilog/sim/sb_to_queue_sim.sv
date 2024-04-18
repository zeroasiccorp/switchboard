// sb_to_queue_sim

// ready_mode settings (in all cases, ready remains low if an outbound packet is stuck)
// ready_mode=0: ready waits for valid before asserting
// ready_mode=1: ready remains asserted as long as an outbound packet is not stuck
// ready_mode=2: ready toggles randomly as long as an outbound packet is not stuck

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_to_queue_sim #(
    parameter integer READY_MODE_DEFAULT=0,
    parameter integer DW=416,
    parameter FILE=""
) (
    input clk,
    input [DW-1:0] data,
    input [31:0] dest,
    input last,
    output reg ready=1'b0,
    input valid
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
    `else
        `define SB_EXT_FUNC(x) x
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction

        import "DPI-C" function void pi_sb_tx_init (output int id,
            input string uri, input int width);
        import "DPI-C" function void pi_sb_send (input int id, input bit [SBDW-1:0] sdata,
            input bit [31:0] sdest, input bit slast, output int success);
    `endif

    // internal signals

    integer id = -1;

    `SB_START_FUNC init(input string uri);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_tx_init)(id, uri, (DW + 7)/8);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    integer success = 0;
    reg pending = 1'b0;

    wire [SBDW-1:0] data_padded;
    generate
        if (SBDW > DW) begin
            assign data_padded = {{(SBDW-DW){1'b0}}, data};
        end else begin
            assign data_padded = data;
        end
    endgenerate

    reg [SBDW-1:0] sdata = 'b0;
    reg [31:0] sdest = 32'b0;
    reg slast = 1'b0;

    // ready mode

    integer ready_mode = READY_MODE_DEFAULT;

    `SB_START_FUNC set_ready_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        ready_mode = value;
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // main logic

    always @(posedge clk) begin
        if (ready && valid) begin
            // try to send a packet, with success==1 indicating that the
            // send was successful.  in general, sends should succeed,
            // unless the queue they're trying to push to is full.
            if (id != -1) begin
                /* verilator lint_off IGNOREDRETURN */
                `SB_EXT_FUNC(pi_sb_send)(id, data_padded, dest, last, success);
                /* verilator lint_on IGNOREDRETURN */
            end else begin
                /* verilator lint_off BLKSEQ */
                success = 32'd0;
                /* verilator lint_on BLKSEQ */
            end

            // if the send was not successful, mark it pending. ready cannot be asserted
            // if there is a pending re-send, since the next send may fail, and there
            // would be no place to store the data for the new resend.  we could have a
            // queue, but that would have finite depth, so we would still have to be able
            // to apply backpressure.
            if (success == 32'd0) begin
                pending <= 1'b1;
                ready <= 1'b0;
                sdata <= data_padded;
                sdest <= dest;
                slast <= last;
            end else begin
                pending <= 1'b0;
                if (ready_mode == 32'd0) begin
                    ready <= 1'b0;
                end else if (ready_mode == 32'd1) begin
                    ready <= 1'b1;
                end else begin
                    /* verilator lint_off WIDTH */
                    ready <= ($random % 2);
                    /* verilator lint_on WIDTH */
                end
            end
        end else if (pending) begin
            // try to re-send a packet.  note that in a given cycle, a packet can be sent
            // for the first time or re-sent, but not both, because ready cannot be asserted
            // if there is a packet pending, for the reason given above.
            if (id != -1) begin
                /* verilator lint_off IGNOREDRETURN */
                `SB_EXT_FUNC(pi_sb_send)(id, sdata, sdest, slast, success);
                /* verilator lint_on IGNOREDRETURN */
            end else begin
                /* verilator lint_off BLKSEQ */
                success = 32'd0;
                /* verilator lint_on BLKSEQ */
            end

            // if the re-send was unsuccessful, we have to keep ready de-asserted,
            // but if it was successful we can assert ready if we want to,
            // depending on ready_mode
            if (success == 32'd0) begin
                pending <= 1'b1;
                ready <= 1'b0;
            end else begin
                pending <= 1'b0;
                if (ready_mode == 32'd0) begin
                    ready <= 1'b0;
                end else if (ready_mode == 32'd1) begin
                    ready <= 1'b1;
                end else begin
                    /* verilator lint_off WIDTH */
                    ready <= ($random % 2);
                    /* verilator lint_on WIDTH */
                end
            end
        end else begin
            // if there's nothing pending, then we can assert ready
            // if we want to.  whether we do or not depends on ready_mode.
            if (ready_mode == 32'd0) begin
                ready <= valid;
            end else if (ready_mode == 32'd1) begin
                ready <= 1'b1;
            end else begin
                /* verilator lint_off WIDTH */
                ready <= ($random % 2);
                /* verilator lint_on WIDTH */
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

endmodule

`default_nettype wire
