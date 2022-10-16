// bridges a single AXI port to one UMI outbound port and one UMI inbound port
// the UMI outbound port sends out both writes and read requests (writes take priority)
// the UMI inbound port is only used for receiving read responses

// NOTE: this is a simple, low-performance implementation - has bubble cycles

`default_nettype none

`timescale 1ns / 1ps

`include "umi_opcodes.vh"

module umi_gpio #(
    parameter integer RWIDTH=32,
    parameter integer WWIDTH=32
) (
    input clk,
    input rst,

    // GPIO interface
    input [(RWIDTH-1):0] gpio_in,
    output reg [(WWIDTH-1):0] gpio_out = '0,

    // UMI outbound interface
    output [255:0] umi_out_packet,
    output reg umi_out_valid = 1'b0,
    input umi_out_ready,

    // UMI inbound interface
    input [255:0] umi_in_packet,
    input umi_in_valid,
    output reg umi_in_ready = 1'b0
);
    // form UMI write packet
    // only data ever written out is a read response

    /* verilator lint_off WIDTH */
    localparam [3:0] UMI_SIZE_WR = $clog2(WWIDTH/8);
    /* verilator lint_on WIDTH */

    reg [63:0] umi_read_resp_addr = '0;
    wire [255:0] umi_write_packet;

    umi_pack umi_pack_i (
        .opcode(`UMI_WRITE_RESPONSE),
        .size(UMI_SIZE_WR),
        .user(20'd0),
        .burst(1'b0),
        .dstaddr(umi_read_resp_addr),
        .srcaddr(64'b0),  // only relevant for read requests...
        .data({{(256-WWIDTH){1'b0}}, gpio_in}),
        .packet(umi_out_packet)
    );

    // can receive a write or a read request

    wire [255:0] umi_in_data;
    wire [63:0] umi_in_dstaddr;
    wire [7:0] umi_in_opcode;
    wire umi_in_cmd_write;
    wire umi_in_cmd_read;
    wire [31:0] umi_in_cmd;

    umi_unpack umi_unpack_i (
        // unpack data
        .packet(umi_in_packet),
        .data(umi_in_data),
        .cmd(umi_in_cmd),

        // unused outputs...
        .dstaddr(),
        .srcaddr()
    );

    /* verilator lint_off PINMISSING */
    umi_decode umi_decode_i (
        .cmd(umi_in_cmd),
        .cmd_read(umi_in_cmd_read),
        .cmd_write(umi_in_cmd_write)
    );
    /* verilator lint_on PINMISSING */

    // main logic

    always @(posedge clk) begin
        if (rst) begin
            // TODO
        end else begin
            // handshaking

            if (umi_out_valid && umi_out_ready) begin
                umi_out_valid <= 1'b0;
            end

            if (umi_in_valid && umi_in_ready) begin
                umi_in_ready <= 1'b0;
            end

            // accept an inbound packet (and possibly generate an outbound
            // packet, if the inbound packet is a read request)

            if (umi_in_valid) begin
                if (!umi_in_ready) begin
                    if (umi_in_cmd_write) begin
                        // ACK the write command and update the GPIO outputs
                        gpio_out <= umi_in_data[(WWIDTH-1):0];
                        umi_in_ready <= 1'b1;
                    end else if (umi_in_cmd_read && (!umi_out_valid)) begin
                        // we can only ACK the read command if we're not currently
                        // trying to respond to a read request.
                        umi_in_ready <= 1'b1;
                        umi_out_valid <= 1'b1;
                    end else begin
                        $display("ERROR: this block only implements reads and writes.");
                        $stop;
                    end
                end
            end
        end
    end

endmodule
