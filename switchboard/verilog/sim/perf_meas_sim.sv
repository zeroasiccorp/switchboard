// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module perf_meas_sim #(
    // verilog_lint: waive-start parameter-name-style
    parameter integer default_cycles_per_meas=0,
    parameter real max_report_time=3.0,
    parameter real min_report_time=0.3,
    parameter integer search_factor=2
    // verilog_lint: waive-stop parameter-name-style
) (
    input clk
);
    `ifdef __ICARUS__
        `define SB_EXT_FUNC(x) $``x``
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
    `else
        `define SB_EXT_FUNC(x) x
        `define SB_START_FUNC function automatic void
        `define SB_END_FUNC endfunction

        import "DPI-C" function void pi_time_taken(output real t);
    `endif

    // internal signals
    real t;
    real sim_rate;
    integer cycles_per_meas=default_cycles_per_meas;
    integer total_clock_cycles=0;
    string sim_name;

    `SB_START_FUNC init(input integer n, input string name="");
        cycles_per_meas = n;
        sim_name = name;
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_time_taken)(t);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        `SB_EXT_FUNC(pi_time_taken)(t);  // discard first result since it is invalid
        /* verilator lint_on IGNOREDRETURN */
    end

    always @(posedge clk) begin
        if (cycles_per_meas == 0) begin
            // do nothing...
        end else if (total_clock_cycles >= cycles_per_meas) begin
            /* verilator lint_off IGNOREDRETURN */
            `SB_EXT_FUNC(pi_time_taken)(t);
            /* verilator lint_on IGNOREDRETURN */
            if (sim_name != "") begin
                $write("%s: ", sim_name);
            end
            sim_rate = (1.0*total_clock_cycles)/t;
            if (sim_rate < 1.0e3) begin
                $display("Simulation rate: %0.3f Hz", sim_rate);
            end else if (sim_rate < 1.0e6) begin
                $display("Simulation rate: %0.3f kHz", 1e-3*sim_rate);
            end else begin
                $display("Simulation rate: %0.3f MHz", 1e-6*sim_rate);
            end
            total_clock_cycles <= 0;

            // update number of cycles in between updates appropriately
            if (t < min_report_time) begin
                // reporting in too frequent, increase cycles_per_meas
                // to report less frequently
                cycles_per_meas = cycles_per_meas * search_factor;
            end else if (t > max_report_time) begin
                // reporting in too infrequent, decrease cycles_per_meas
                // to report more frequently
                cycles_per_meas = cycles_per_meas / search_factor;
                if (cycles_per_meas == 0) begin
                    // but don't let cycles_per_meas drop to zero,
                    // since that disables performance measurement
                    cycles_per_meas = 1;
                end
            end
        end else begin
            total_clock_cycles <= total_clock_cycles + 1;
        end
    end

    // clean up macros

    `undef SB_EXT_FUNC
    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule

`default_nettype wire
