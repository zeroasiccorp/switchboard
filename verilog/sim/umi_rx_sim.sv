`default_nettype none

module umi_rx_sim #(
    parameter integer VALID_MODE_DEFAULT=0
) (
    input clk,
    output [255:0] packet,
    input ready,
    output valid
);

    sb_rx_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT)
    ) rx_i (
        .clk(clk),
        .data(packet),
        .dest(),
        .last(),
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
        rx_i.init(uri);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // clean up macros

    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule

`default_nettype wire
