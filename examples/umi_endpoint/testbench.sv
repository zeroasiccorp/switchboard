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
    parameter integer CW=32;
    parameter integer AW=64;

    `SWITCHBOARD_SIM_PORT(udev, DW);

    reg nreset = 1'b0;
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

    umi_endpoint umi_endpoint_i (
        .*
    );

    always @(posedge clk) begin
        nreset <= 1'b1;
    end

    // memory backing

    reg [63:0] mem [256];

    always @(posedge clk) begin
        loc_rddata <= {192'd0, mem[loc_addr[7:0]]};
    end

    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            // do nothing
        end else if (loc_write) begin
            mem[loc_addr[7:0]] <= loc_wrdata[63:0];
        end
    end

    // Waveforms

    `SB_SETUP_PROBES();

endmodule

`default_nettype wire
