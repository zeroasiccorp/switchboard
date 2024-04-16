// Universal Memory Interface (UMI) GPIO

// The output gpio_out is "updated" by any write to this module, and the
// input "gpio_in" is read out by any read from this module.

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module umi_gpio #(
    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32,
    parameter integer IWIDTH=32,
    parameter integer OWIDTH=32,
    parameter [OWIDTH-1:0] INITVAL=0
) (
    input clk,
    input nreset,

    // GPIO interface
    input [IWIDTH-1:0] gpio_in,
    output [OWIDTH-1:0] gpio_out,

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

    `include "umi_messages.vh"

    // interpret incoming packet

    wire [4:0]   req_opcode;
    wire [2:0]   req_size;
    wire [7:0]   req_len;
    wire [7:0]   req_atype;
    wire [3:0]   req_qos;
    wire [1:0]   req_prot;
    wire         req_eom;
    wire         req_eof;
    wire         req_ex;
    wire [1:0]   req_user;
    wire [23:0]  req_user_extended;
    wire [1:0]   req_err;
    wire [4:0]   req_hostid;

    /* verilator lint_off PINMISSING */
    umi_unpack #(
        .CW(CW)
    ) umi_unpack_i (
        .packet_cmd(udev_req_cmd),
        .cmd_opcode(req_opcode),
        .cmd_size(req_size),
        .cmd_len(req_len),
        .cmd_atype(req_atype),
        .cmd_qos(req_qos),
        .cmd_prot(req_prot),
        .cmd_eom(req_eom),
        .cmd_eof(req_eof),
        .cmd_ex(req_ex),
        .cmd_user(req_user),
        .cmd_user_extended(req_user_extended),
        .cmd_err(req_err),
        .cmd_hostid(req_hostid)
    );
    /* verilator lint_on PINMISSING */

    wire req_cmd_read;
    assign req_cmd_read = (req_opcode == UMI_REQ_READ) ? 1'b1 : 1'b0;

    wire req_cmd_write;
    assign req_cmd_write = (req_opcode == UMI_REQ_WRITE) ? 1'b1 : 1'b0;

    wire req_cmd_posted;
    assign req_cmd_posted = (req_opcode == UMI_REQ_POSTED) ? 1'b1 : 1'b0;

    // form outgoing packet (which can only be a read response)

    reg [4:0]   resp_opcode;
    reg [2:0]   resp_size;
    reg [7:0]   resp_len;
    reg [7:0]   resp_atype;
    reg [3:0]   resp_qos;
    reg [1:0]   resp_prot;
    reg         resp_eom;
    reg         resp_eof;
    reg         resp_ex;
    reg [1:0]   resp_user;
    reg [23:0]  resp_user_extended;
    reg [1:0]   resp_err;
    reg [4:0]   resp_hostid;

    umi_pack #(
        .CW(CW)
    ) umi_pack_i (
        .cmd_opcode(resp_opcode),
        .cmd_size(resp_size),
        .cmd_len(resp_len),
        .cmd_atype(resp_atype),
        .cmd_prot(resp_prot),
        .cmd_qos(resp_qos),
        .cmd_eom(resp_eom),
        .cmd_eof(resp_eof),
        .cmd_user(resp_user),
        .cmd_err(resp_err),
        .cmd_ex(resp_ex),
        .cmd_hostid(resp_hostid),
        .cmd_user_extended(resp_user_extended),
        .packet_cmd(udev_resp_cmd)
    );

    // main logic

    reg [OWIDTH-1:0] gpio_out_r;
    assign gpio_out = gpio_out_r;

    reg [31:0] read_bytes_remaining;
    reg resp_in_progress;
    reg [AW-1:0] read_dstaddr;

    wire [31:0] nbytes;
    assign nbytes = (resp_in_progress ? read_bytes_remaining :
        ({24'd0, req_len} + 32'd1)*(32'd1<<{29'd0, req_size}));

    wire [31:0] flit_bytes;
    assign flit_bytes = (nbytes <= (DW/8)) ? nbytes : (DW/8);

    wire [31:0] resp_len_req_next32 = {((flit_bytes >> req_size) - 32'd1)};
    wire [7:0] resp_len_req_next = resp_len_req_next32[7:0];

    wire [31:0] resp_len_next32 = {((flit_bytes >> resp_size) - 32'd1)};
    wire [7:0] resp_len_next = resp_len_next32[7:0];

    reg active;
    assign udev_req_ready = (active
        && (!((udev_resp_valid && (!udev_resp_ready)) || resp_in_progress)));

    reg udev_resp_valid_r;
    assign udev_resp_valid = udev_resp_valid_r;

    reg [DW-1:0] udev_resp_data_r;
    assign udev_resp_data = udev_resp_data_r;

    reg [AW-1:0] udev_resp_dstaddr_r;
    assign udev_resp_dstaddr = udev_resp_dstaddr_r;

    integer i;

    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            active <= 1'b0;
        end else begin
            active <= 1'b1;
        end
    end

    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            gpio_out_r <= INITVAL;
            read_bytes_remaining <= 'd0;
            resp_in_progress <= 1'b0;
            read_dstaddr <= 'd0;
            udev_resp_valid_r <= 1'b0;
        end else if (udev_req_valid && udev_req_ready) begin
            if (req_cmd_posted || req_cmd_write) begin
                for (i=0; i<flit_bytes; i=i+1) begin
                    gpio_out_r[(i[$clog2(OWIDTH)-1:0]+udev_req_dstaddr[$clog2(OWIDTH)-1:0])*8 +: 8]
                        <= udev_req_data[i*8 +: 8];
                end
                if (req_cmd_write) begin
                    resp_opcode <= UMI_RESP_WRITE;
                    udev_resp_valid_r <= 1'b1;
                end
            end else if (req_cmd_read) begin
                for (i=0; i<flit_bytes; i=i+1) begin
                    udev_resp_data_r[i*8 +: 8] <=
                      gpio_in[(i[$clog2(IWIDTH)-1:0]+udev_req_dstaddr[$clog2(IWIDTH)-1:0])*8 +: 8];
                end
                resp_opcode <= UMI_RESP_READ;
                udev_resp_valid_r <= 1'b1;
                if (nbytes > (DW/8)) begin
                    resp_in_progress <= 1'b1;
                    read_bytes_remaining <= nbytes - flit_bytes;
                    read_dstaddr <= udev_req_dstaddr + {{(AW-32){1'b0}}, flit_bytes};
                end
            end

            // pass through data
            resp_size <= req_size;
            resp_len <= resp_len_req_next;
            resp_atype <= req_atype;
            resp_prot <= req_prot;
            resp_qos <= req_qos;
            resp_eom <= (nbytes <= (DW/8)) ? 1'b1 : 1'b0;
            resp_eof <= req_eof;
            resp_user <= req_user;
            resp_err <= req_err;
            resp_ex <= req_ex;
            resp_hostid <= req_hostid;
            resp_user_extended <= req_user_extended;
            udev_resp_dstaddr_r <= udev_req_srcaddr;
        end else if (udev_resp_valid && udev_resp_ready) begin
            if (resp_in_progress) begin
                if (read_bytes_remaining == 'd0) begin
                    udev_resp_valid_r <= 1'b0;
                    resp_in_progress <= 1'b0;
                end else begin
                    read_bytes_remaining <= read_bytes_remaining - flit_bytes;
                    resp_len <= resp_len_next;
                    udev_resp_dstaddr_r <= udev_resp_dstaddr + {{(AW-32){1'b0}}, flit_bytes};
                    read_dstaddr <= read_dstaddr + {{(AW-32){1'b0}}, flit_bytes};
                    resp_eom <= (read_bytes_remaining <= (DW/8)) ? 1'b1 : 1'b0;
                    for (i=0; i<flit_bytes; i=i+1) begin
                        udev_resp_data_r[i*8 +: 8] <=
                          gpio_in[(i[$clog2(IWIDTH)-1:0]+read_dstaddr[$clog2(IWIDTH)-1:0])*8 +: 8];
                    end
                end
            end else begin
                udev_resp_valid_r <= 1'b0;
            end
        end
    end

endmodule
