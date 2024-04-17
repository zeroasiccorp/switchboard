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
    localparam integer IWIDTH=384;
    localparam integer OWIDTH=128;

    `SB_UMI_WIRES(udev_req, DW, CW, AW);
    `QUEUE_TO_UMI_SIM(udev_req, DW, CW, AW, "to_rtl.q");

    `SB_UMI_WIRES(udev_resp, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(udev_resp, DW, CW, AW, "from_rtl.q");

    reg nreset = 1'b0;
    wire [(IWIDTH-1):0] gpio_in;
    wire [(OWIDTH-1):0] gpio_out;

    umi_gpio #(
        .DW(DW),
        .AW(AW),
        .CW(CW),
        .IWIDTH(IWIDTH),
        .OWIDTH(OWIDTH)
    ) umi_gpio_i (
        .*
    );

    always @(posedge clk) begin
        nreset <= 1'b1;
    end

    // operations

    assign gpio_in[ 7:0] = gpio_out[ 7:0] + 8'd12;
    assign gpio_in[15:8] = gpio_out[15:8] - 8'd34;

    assign gpio_in[255:128] = gpio_out[127:0];
    assign gpio_in[383:256] = ~gpio_out[127:0];

    // Waveforms

    `SB_SETUP_PROBES

endmodule

`default_nettype wire
