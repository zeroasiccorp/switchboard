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
    `QUEUE_TO_UMI_SIM(rx_i, udev_req, clk, DW, CW, AW);

    `SB_UMI_WIRES(udev_resp, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx_i, udev_resp, clk, DW, CW, AW);

    // instantiate module with UMI ports

    umiram ram_i (
        .*
    );

    // Initialize UMI

    initial begin
        rx_i.init("to_rtl.q");
        tx_i.init("from_rtl.q");
    end

    // Waveforms

    `SB_PROBE

endmodule

`default_nettype wire
