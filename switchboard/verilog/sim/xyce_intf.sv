// Module for interfacing with Xyce analog simulation

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module xyce_intf;
    timeprecision 1fs;

    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask

        timeunit 1s;
        `define SB_ABSTIME ($realtime)
    `else
        `define SB_EXT_FUNC(x) x
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
        `define SB_ABSTIME ($realtime/1s)

        import "DPI-C" function void pi_sb_xyce_init (
            output int id,
            input string file
        );
        import "DPI-C" function void pi_sb_xyce_put (
            input int id,
            input string name,
            input real t,
            input real value
        );
        import "DPI-C" function void pi_sb_xyce_get (
            input int id,
            input string name,
            input real t,
            output real value
        );
    `endif

    integer id = -1;

   `SB_START_FUNC init(input string file);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_init)(id, file);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

   `SB_START_FUNC put(input string name, input real value);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_put)(id, name, `SB_ABSTIME, value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

   `SB_START_FUNC get(input string name, output real value);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_get)(id, name, `SB_ABSTIME, value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_START_FUNC
    `undef SB_END_FUNC
    `undef SB_ABSTIME

endmodule
