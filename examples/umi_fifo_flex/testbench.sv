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

        reg clk;
        always begin
            clk = 1'b0;
            #5;
            clk = 1'b1;
            #5;
        end

    `endif

    parameter integer IDW=256;
    parameter integer ODW=64;
    parameter integer AW=64;
    parameter integer CW=32;

    `SB_UMI_WIRES(udev_req, IDW, CW, AW);
    `QUEUE_TO_UMI_SIM(rx_i, udev_req, clk, IDW, CW, AW);

    `SB_UMI_WIRES(udev_resp, ODW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx_i, udev_resp, clk, ODW, CW, AW);

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

    // Initialize UMI

    initial begin
        rx_i.init("to_rtl.q");
        tx_i.init("from_rtl.q");
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
