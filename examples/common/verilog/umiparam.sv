// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

`include "switchboard.vh"

module umiparam #(
    parameter DW=32,
    parameter CW=32,
    parameter AW=64
) (
    input clk,
    input nreset,
    input [DW-1:0] value,
    `SB_UMI_INPUT(udev_req, DW, CW, AW),
    `SB_UMI_OUTPUT(udev_resp, DW, CW, AW)
);
    wire [AW-1:0] loc_addr;
    wire          loc_write;
    wire          loc_read;
    wire [7:0]    loc_opcode;
    wire [2:0]    loc_size;
    wire [7:0]    loc_len;
    wire [DW-1:0] loc_wrdata;
    reg  [DW-1:0] loc_rddata;
    wire          loc_ready;
    wire          loc_atomic;
    wire [7:0]    loc_atype;

    assign loc_ready = nreset;

    umi_endpoint #(
        .DW(DW),
        .CW(CW),
        .AW(AW)
    ) umi_endpoint_i (
        .*
    );

    // register implementation

    assign loc_rddata = value;

endmodule

`default_nettype wire
