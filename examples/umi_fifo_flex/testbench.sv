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

    parameter integer IDW=256;
    parameter integer ODW=64;
    parameter integer AW=64;
    parameter integer CW=32;

    `SB_UMI_WIRES(udev_req, IDW, CW, AW);
    `QUEUE_TO_UMI_SIM(udev_req, IDW, CW, AW, "to_rtl.q");

    `SB_UMI_WIRES(udev_resp, ODW, CW, AW);
    `UMI_TO_QUEUE_SIM(udev_resp, ODW, CW, AW, "from_rtl.q");

    reg nreset = 1'b0;

    umi_fifo_flex #(
        .IDW(IDW),
        .ODW(ODW)
    ) umi_fifo_flex_i (
        .bypass(1'b0),
        .chaosmode(1'b0),
        .fifo_full(),
        .fifo_empty(),
        // Input UMI
        .umi_in_clk(clk),
        .umi_in_nreset(nreset),
        `SB_UMI_CONNECT(umi_in, udev_req),
        // Output UMI
        .umi_out_clk(clk),
        .umi_out_nreset(nreset),
        `SB_UMI_CONNECT(umi_out, udev_resp),
        // Supplies
        .vdd(1'b1),
        .vss(1'b0)
    );

    always @(posedge clk) begin
        nreset <= 1'b1;
    end

    // Waveforms

    `SB_SETUP_PROBES

endmodule

`default_nettype wire
