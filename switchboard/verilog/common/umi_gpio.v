/*******************************************************************************
 * Function:  Universal Memory Interface (UMI) GPIO
 * Author:    Steven Herbst
 * License:   (c) 2023 Zero ASIC. All rights reserved.
 *
 * Documentation:
 *
 * The output gpio_out is updated by any write to this module, and the
 * input gpio_in is read out by any read from this module.
 *
 ******************************************************************************/

module umi_gpio #(
    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32,
    parameter integer RWIDTH=32,
    parameter integer WWIDTH=32
) (
    input clk,
    input nreset,

    // GPIO interface
    input [RWIDTH-1:0] gpio_in,
    output [WWIDTH-1:0] gpio_out,

    // UMI inbound interface
    input           udev_req_valid,
    input [CW-1:0]  udev_req_cmd,
    input [AW-1:0]  udev_req_dstaddr,
    input [AW-1:0]  udev_req_srcaddr,
    input [DW-1:0]  udev_req_data,
    output          udev_req_ready,

    // UMI outbound interface
    output          udev_resp_valid,
    output [CW-1:0] udev_resp_cmd,
    output [AW-1:0] udev_resp_dstaddr,
    output [AW-1:0] udev_resp_srcaddr,
    output [DW-1:0] udev_resp_data,
    input           udev_resp_ready
);
    // UMI endpoint

    wire [AW-1:0] loc_addr;
    wire          loc_write;
    wire          loc_read;
    wire [7:0]    loc_opcode;
    wire [2:0]    loc_size;
    wire [7:0]    loc_len;
    wire [DW-1:0] loc_wrdata;
    wire [DW-1:0] loc_rddata;
    wire          loc_ready;

    assign loc_ready = nreset;

    umi_endpoint #(
        .AW(AW),
        .DW(DW),
        .CW(CW)
    ) umi_endpoint_i (
        .nreset(nreset),
        .clk(clk),
        .udev_req_valid(udev_req_valid),
        .udev_req_cmd(udev_req_cmd),
        .udev_req_dstaddr(udev_req_dstaddr),
        .udev_req_srcaddr(udev_req_srcaddr),
        .udev_req_data(udev_req_data),
        .udev_req_ready(udev_req_ready),
        .udev_resp_valid(udev_resp_valid),
        .udev_resp_cmd(udev_resp_cmd),
        .udev_resp_dstaddr(udev_resp_dstaddr),
        .udev_resp_srcaddr(udev_resp_srcaddr),
        .udev_resp_data(udev_resp_data),
        .udev_resp_ready(udev_resp_ready),
        .loc_addr(loc_addr),
        .loc_write(loc_write),
        .loc_read(loc_read),
        .loc_opcode(loc_opcode),
        .loc_size(loc_size),
        .loc_len(loc_len),
        .loc_wrdata(loc_wrdata),
        .loc_rddata(loc_rddata),
        .loc_ready(loc_ready)
    );

    // custom logic

    assign loc_rddata[RWIDTH-1:0] = gpio_in;

    reg [(WWIDTH-1):0] gpio_out_r;
    assign gpio_out = gpio_out_r;

    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            gpio_out_r <= '0;
        end else if (loc_write) begin
            gpio_out_r <= loc_wrdata[WWIDTH-1:0];
        end
    end

endmodule
