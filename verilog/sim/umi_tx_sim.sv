`default_nettype none

module umi_tx_sim #(
    parameter integer READY_MODE_DEFAULT=0
) (
    input clk,
    input [255:0] packet,
    output ready,
    input valid
);

    // TODO: support burst mode (through "last")

    sb_tx_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT)
    ) tx_i (
        .clk(clk),
        .data(packet),
        .dest({16'h0000, packet[255:240]}),
        .last(1'b1),
        .ready(ready),
        .valid(valid)
    );

    // handle differences between simulators

    `ifdef __ICARUS__
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
    `else
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
    `endif

    `SB_START_FUNC init(input string uri);
        /* verilator lint_off IGNOREDRETURN */
        tx_i.init(uri);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // clean up macros

    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule

`default_nettype wire
