// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module testbench (
    input clk
);

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

    reg nreset = 1'b0;

    queue_to_umi_sim #(
        .VALID_MODE_DEFAULT(2)
    ) rx_i (
        .clk(clk),
        .data(udev_req_data),
        .srcaddr(udev_req_srcaddr),
        .dstaddr(udev_req_dstaddr),
        .cmd(udev_req_cmd),
        .ready(udev_req_ready),
        .valid(udev_req_valid)
    );

    umi_to_queue_sim #(
        .READY_MODE_DEFAULT(2)
    ) tx_i (
        .clk(clk),
        .data(udev_resp_data),
        .srcaddr(udev_resp_srcaddr),
        .dstaddr(udev_resp_dstaddr),
        .cmd(udev_resp_cmd),
        .ready(udev_resp_ready),
        .valid(udev_resp_valid)
    );

    umi_fifo_flex #(
        .IDW(256),
        .ODW(64)
    ) umi_fifo_flex_i (
        .bypass(1'b0),
        .chaosmode(1'b0),
        .fifo_full(),
        .fifo_empty(),
        // Input UMI
        .umi_in_clk(clk),
        .umi_in_nreset(nreset),
        .umi_in_valid(udev_req_valid),
        .umi_in_cmd(udev_req_cmd),
        .umi_in_dstaddr(udev_req_dstaddr),
        .umi_in_srcaddr(udev_req_srcaddr),
        .umi_in_data(udev_req_data),
        .umi_in_ready(udev_req_ready),
        // Output UMI
        .umi_out_clk(clk),
        .umi_out_nreset(nreset),
        .umi_out_valid(udev_resp_valid),
        .umi_out_cmd(udev_resp_cmd),
        .umi_out_dstaddr(udev_resp_dstaddr),
        .umi_out_srcaddr(udev_resp_srcaddr),
        .umi_out_data(udev_resp_data[63:0]),
        .umi_out_ready(udev_resp_ready),
        // Supplies
        .vdd(1'b1),
        .vss(1'b0)
    );

    always @(posedge clk) begin
        nreset <= 1'b1;
    end

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("client2rtl.q");
        tx_i.init("rtl2client.q");
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
