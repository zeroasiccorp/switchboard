// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

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

    wire           udev_req_valid;
    wire           udev_req_ready;
    wire [CW-1:0]  udev_req_cmd;
    wire [AW-1:0]  udev_req_dstaddr;
    wire [AW-1:0]  udev_req_srcaddr;
    wire [DW-1:0]  udev_req_data;

    wire          udev_resp_valid;
    wire          udev_resp_ready;
    wire [CW-1:0] udev_resp_cmd;
    wire [AW-1:0] udev_resp_dstaddr;
    wire [AW-1:0] udev_resp_srcaddr;
    wire [DW-1:0] udev_resp_data;

    queue_to_umi_sim rx_i (
        .clk(clk),
        .data(udev_req_data),
        .srcaddr(udev_req_srcaddr),
        .dstaddr(udev_req_dstaddr),
        .cmd(udev_req_cmd),
        .ready(udev_req_ready),
        .valid(udev_req_valid)
    );

    umi_to_queue_sim tx_i (
        .clk(clk),
        .data(udev_resp_data),
        .srcaddr(udev_resp_srcaddr),
        .dstaddr(udev_resp_dstaddr),
        .cmd(udev_resp_cmd),
        .ready(udev_resp_ready),
        .valid(udev_resp_valid)
    );

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
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("to_rtl.q");
        tx_i.init("from_rtl.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // Waveforms

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

    // auto-stop

    auto_stop_sim auto_stop_sim_i (.clk(clk));

endmodule

`default_nettype wire
