// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

`include "switchboard.vh"

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    parameter integer DW=256;
    parameter integer AW=64;
    parameter integer CW=32;

    // clock
    `ifndef VERILATOR

        reg clk;
        always begin
            clk = 1'b0;
            #5;
            clk = 1'b1;
            #5;
        end

    `endif

    // UMI input

    `SB_UMI_WIRES(umi_in, DW, CW, AW);
    `QUEUE_TO_UMI_SIM(rx, umi_in, clk, DW, CW, AW);

    // UMI output (response)

    `SB_UMI_WIRES(umi_resp_out, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx0, umi_resp_out, clk, DW, CW, AW);

    // UMI output (request)

    `SB_UMI_WIRES(umi_req_out, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx1, umi_req_out, clk, DW, CW, AW);

    // UMI splitter

    umi_splitter umi_splitter_i (
        .*
    );

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx.init("in.q");
        tx0.init("out0.q");
        tx1.init("out1.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // Waveforms

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

endmodule

`default_nettype wire
