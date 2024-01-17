// Module for interfacing with Xyce analog simulation

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module xyce_intf;
    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
    `else
        `define SB_EXT_FUNC(x) x
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction

        import "DPI-C" function void pi_sb_xyce_init (input string file);
        import "DPI-C" function void pi_sb_xyce_advance (input real dt);
        import "DPI-C" function void pi_sb_xyce_put (input string name, input real value);
        import "DPI-C" function void pi_sb_xyce_get (input string name, output real value);
    `endif

   `SB_START_FUNC init(input string file);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_init)(file);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

   `SB_START_FUNC advance(input real dt);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_advance)(dt);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

   `SB_START_FUNC put(input string name, input real value);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_put)(name, value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

   `SB_START_FUNC get(input string name, output real value);
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_sb_xyce_get)(name, value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule
