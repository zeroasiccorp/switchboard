`default_nettype none

module sb_tx_sim (
    input clk,
    input [255:0] data,
    input [31:0] dest,
    input last,
    output ready,
    input valid
);
    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
        `define SB_WIRE_BIT wire
    `else
        `define SB_EXT_FUNC(x) ``x``
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
        `define SB_WIRE_BIT wire bit

        import "DPI-C" function void pi_sb_tx_init (output int id, input string uri);
        import "DPI-C" function void pi_sb_send (input int id, input bit [255:0] sdata,
            input bit [31:0] sdest, input bit slast, output int success);
    `endif

    // internal signals

    integer id = -1;
    integer success = 0;
    reg in_progress = 1'b0;
    reg ready_reg = 1'b0;


    `SB_START_FUNC init(input string uri);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_tx_init)(id, uri);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_WIRE_BIT [255:0] sdata;
    `SB_WIRE_BIT [31:0] sdest;
    `SB_WIRE_BIT slast;

    // main logic

    always @(posedge clk) begin
        if (in_progress) begin
            ready_reg <= 1'b0;
            in_progress <= 1'b0;
        end else begin
            if (valid) begin
                if (id != -1) begin
                    /* verilator lint_off IGNOREDRETURN */
                    `SB_EXT_FUNC(pi_sb_send)(id, sdata, sdest, slast, success);
                    /* verilator lint_on IGNOREDRETURN */
                end else begin
                    success = 32'd0;
                end
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

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_START_FUNC
    `undef SB_END_FUNC
    `undef SB_WIRE_BIT

endmodule

`default_nettype wire
