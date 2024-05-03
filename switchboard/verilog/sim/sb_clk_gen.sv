// Module for generating a simulation clock, needed for non-Verilator simulations

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module sb_clk_gen #(
    parameter real DEFAULT_PERIOD = 10e-9,
    parameter real DEFAULT_DUTY_CYCLE = 0.5,
    parameter real DEFAULT_MAX_RATE = -1,
    parameter real DEFAULT_START_DELAY = -1
) (
    output wire clk
);
    // configure timing

    `ifdef SB_XYCE
        timeunit 1s;
        timeprecision 1fs;
        `define SB_DELAY(t) #(t)
    `else
        timeunit 1ns;
        timeprecision 1ns;
        `define SB_DELAY(t) #((t)*1e9)
    `endif

    // import external functions

    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
    `else
        `define SB_EXT_FUNC(x) x

        import "DPI-C" function void pi_start_delay (
            input real value
        );

        import "DPI-C" function void pi_max_rate_tick (
            inout signed [63:0] t_us,
            input signed [63:0] min_period_us
        );
    `endif

    // read in command-line arguments

    real period = DEFAULT_PERIOD;
    real duty_cycle = DEFAULT_DUTY_CYCLE;
    real max_rate = DEFAULT_MAX_RATE;
    real start_delay = DEFAULT_START_DELAY;

    reg signed [63:0] t_us = -(64'sd1);
    reg signed [63:0] min_period_us = -(64'sd1);

    initial begin
        void'($value$plusargs("period=%f", period));
        void'($value$plusargs("duty-cycle=%f", duty_cycle));
        void'($value$plusargs("start-delay=%f", start_delay));

        void'($value$plusargs("max-rate=%f", max_rate));

        if (max_rate > 0) begin
            min_period_us = 1.0e6 / max_rate;  // rounds according to LRM
        end
    end

    // main clock generation code

    reg clk_r;
    assign clk = clk_r;

    initial begin
        `SB_EXT_FUNC(pi_start_delay)(start_delay);

        forever begin
            `SB_EXT_FUNC(pi_max_rate_tick)(t_us, min_period_us);

            clk_r = 1'b0;
            `SB_DELAY((1.0 - duty_cycle) * period);

            clk_r = 1'b1;
            `SB_DELAY(duty_cycle * period);
        end
    end

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_DELAY

endmodule
