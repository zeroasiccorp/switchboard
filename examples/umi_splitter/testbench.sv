// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

`include "switchboard.vh"

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    `ifndef VERILATOR
        `SB_CREATE_CLOCK(clk)
    `endif

    localparam integer DW=256;
    localparam integer AW=64;
    localparam integer CW=32;

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
        rx.init("in.q");
        tx0.init("out0.q");
        tx1.init("out1.q");
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
