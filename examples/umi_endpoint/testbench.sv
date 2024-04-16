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

    parameter integer DW=256;
    parameter integer CW=32;
    parameter integer AW=64;

    `SB_UMI_WIRES(udev_req, DW, CW, AW);
    `QUEUE_TO_UMI_SIM(rx_i, udev_req, clk, DW, CW, AW);

    `SB_UMI_WIRES(udev_resp, DW, CW, AW);
    `UMI_TO_QUEUE_SIM(tx_i, udev_resp, clk, DW, CW, AW);

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
