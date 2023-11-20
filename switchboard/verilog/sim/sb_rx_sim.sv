// Wrapper module for backwards compatibility (will eventually be removed)

// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_rx_sim #(
    parameter integer VALID_MODE_DEFAULT=0,
    parameter integer DW=416
) (
    input clk,
    output [DW-1:0] data,
    output [31:0] dest,
    output last,
    input ready,
    output valid
);
    `ifdef __ICARUS__
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
    `else
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
    `endif

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(DW)
    ) rx_i (
        .*
    );

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
