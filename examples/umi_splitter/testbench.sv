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
    `QUEUE_TO_UMI_SIM(umi_in, DW, CW, AW, "in.q");

    // UMI output (response)

    `SB_UMI_WIRES(umi_resp_out, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(umi_resp_out, DW, CW, AW, "out0.q");

    // UMI output (request)

    `SB_UMI_WIRES(umi_req_out, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(umi_req_out, DW, CW, AW, "out1.q");

    // UMI splitter

    umi_splitter umi_splitter_i (
        .*
    );

    // Waveforms

    `SB_SETUP_PROBES

endmodule

`default_nettype wire
