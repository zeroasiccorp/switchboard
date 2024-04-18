// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module queue_to_umi_sim #(
    parameter integer VALID_MODE_DEFAULT=0,
    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32,
    parameter FILE=""
) (
    input clk,
    output [DW-1:0] data,
    output [AW-1:0] srcaddr,
    output [AW-1:0] dstaddr,
    output [CW-1:0] cmd,
    input ready,
    output valid
);

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(DW+AW+AW+CW),
        .FILE(FILE)
    ) rx_i (
        .clk(clk),
        .data({data, srcaddr, dstaddr, cmd}),
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

    `SB_START_FUNC set_valid_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        rx_i.set_valid_mode(value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // clean up macros

    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule

`default_nettype wire
