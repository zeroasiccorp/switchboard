// Copyright (c) 2023 Zero ASIC Corporation
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

    parameter integer DW=256;
    parameter integer AW=64;
    parameter integer CW=32;

    `SB_UMI_WIRES(udev_req, DW, CW, AW);
    `QUEUE_TO_UMI_SIM(rx_i, udev_req, clk, DW, CW, AW);

    `SB_UMI_WIRES(udev_resp, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx_i, udev_resp, clk, DW, CW, AW);

    // instantiate module with UMI ports

    umiram ram_i (
        .*
    );

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("to_rtl.q");
        tx_i.init("from_rtl.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // Waveforms

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.fst");
            $dumpvars(0, testbench);
        end
    end

endmodule

`default_nettype wire
