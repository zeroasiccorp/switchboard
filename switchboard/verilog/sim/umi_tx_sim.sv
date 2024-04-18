// Wrapper module for backwards compatibility (will eventually be removed)

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module umi_tx_sim #(
    parameter integer READY_MODE_DEFAULT=0,
    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32,
    parameter FILE=""
) (
    input clk,
    input [DW-1:0] data,
    input [AW-1:0] srcaddr,
    input [AW-1:0] dstaddr,
    input [CW-1:0] cmd,
    output ready,
    input valid
);

    `ifdef __ICARUS__
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
    `else
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
    `endif

    umi_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(DW),
        .AW(AW),
        .CW(CW),
        .FILE(FILE)
    ) tx_i (
        .*
    );

    `SB_START_FUNC init(input string uri);
        /* verilator lint_off IGNOREDRETURN */
        tx_i.init(uri);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_START_FUNC set_ready_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        tx_i.set_ready_mode(value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // clean up macros

    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule

`default_nettype wire
