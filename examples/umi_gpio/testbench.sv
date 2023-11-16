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
    parameter integer IWIDTH=384;
    parameter integer OWIDTH=128;

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
