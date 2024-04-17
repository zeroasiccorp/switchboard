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

    `SB_UMI_WIRES(udev_req, DW, CW, AW);
    `QUEUE_TO_UMI_SIM(rx_i, udev_req, clk, DW, CW, AW, "to_rtl.q");

    `SB_UMI_WIRES(udev_resp, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx_i, udev_resp, clk, DW, CW, AW, "from_rtl.q");

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
        // input
        .umi_in_clk(clk),
        .umi_in_nreset(nreset),
        `SB_UMI_CONNECT(umi_in, udev_req),
        // output
        .umi_out_clk(clk),
        .umi_out_nreset(nreset),
        `SB_UMI_CONNECT(umi_out, udev_resp),
        // supplies
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
