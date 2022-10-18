`default_nettype none

module sb_rx_sim (
    input clk,
    output reg [255:0] data=256'b0,
    output reg [31:0] dest=32'b0,
    output reg last=1'b0,
    input ready,
    output reg valid=1'b0
);
    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
        `define SB_VAR_BIT reg
    `else
        `define SB_EXT_FUNC(x) ``x``
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
        `define SB_VAR_BIT var bit

        import "DPI-C" function void pi_sb_rx_init(output int id, input string uri);
        import "DPI-C" function void pi_sb_recv(input int id, output bit [255:0] rdata,
            output bit [31:0] rdest, output bit rlast, output int success);
    `endif

    // internal signals

    integer id = -1;
    integer success = 0;
    reg in_progress = 1'b0;

    `SB_START_FUNC init(input string uri);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_rx_init)(id, uri);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_VAR_BIT [255:0] rdata;
    `SB_VAR_BIT [31:0] rdest;
    `SB_VAR_BIT rlast;

    initial begin
        rdata = 256'b0;
        rdest = 32'b0;
        rlast = 1'b0;
    end

    // main logic

    always @(posedge clk) begin
        if (in_progress) begin
            if (ready) begin
                valid <= 1'b0;
                in_progress <= 1'b0;
            end
        end else begin
            if (id != -1) begin
                /* verilator lint_off IGNOREDRETURN */
                `SB_EXT_FUNC(pi_sb_recv)(id, rdata, rdest, rlast, success);
                /* verilator lint_on IGNOREDRETURN */
            end else begin
                success = 32'd0;
            end
            if (success == 32'd1) begin
                valid <= 1'b1;
                in_progress <= 1'b1;
                data <= rdata;
                dest <= rdest;
                last <= rlast;
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
