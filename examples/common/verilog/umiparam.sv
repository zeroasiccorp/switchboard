// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module umiparam #(
    parameter DW=32,
    parameter CW=32,
    parameter AW=64
) (
    input clk,
    input nreset,

    input [DW-1:0] value,
    input udev_req_valid,
    output udev_req_ready,
    input [CW-1:0] udev_req_cmd,
    input [AW-1:0] udev_req_dstaddr,
    input [AW-1:0] udev_req_srcaddr,
    input [DW-1:0] udev_req_data,

    output udev_resp_valid,
    input udev_resp_ready,
    output [CW-1:0] udev_resp_cmd,
    output [AW-1:0] udev_resp_dstaddr,
    output [AW-1:0] udev_resp_srcaddr,
    output [DW-1:0] udev_resp_data
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
