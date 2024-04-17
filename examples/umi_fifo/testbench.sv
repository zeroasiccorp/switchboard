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

    parameter integer DW=256;
    parameter integer AW=64;
    parameter integer CW=32;

    `SB_UMI_WIRES(udev_req, DW, CW, AW);
    `QUEUE_TO_UMI_SIM(rx_i, udev_req, clk, DW, CW, AW);

    `SB_UMI_WIRES(udev_resp, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx_i, udev_resp, clk, DW, CW, AW);

    reg nreset = 1'b0;

    umi_fifo #(
        .DW(DW),
        .CW(CW),
        .AW(AW)
    ) umi_fifo_i (
        .bypass(1'b1),
        .chaosmode(1'b0),
        .fifo_full(),
        .fifo_empty(),
        .umi_in_clk(clk),
        .umi_in_nreset(nreset),
        `SB_UMI_CONNECT(umi_in, udev_req),
        // Output
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

    // Initialize UMI

    initial begin
        rx_i.init("to_rtl.q");
        tx_i.init("from_rtl.q");
    end

    // Waveforms

    `SB_PROBE

endmodule

`default_nettype wire
