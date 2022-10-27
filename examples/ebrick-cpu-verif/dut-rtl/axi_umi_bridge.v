// bridges a single AXI port to one UMI outbound port and one UMI inbound port
// the UMI outbound port sends out both writes and read requests (writes take priority)
// the UMI inbound port is only used for receiving read responses

// NOTE: this is a simple, low-performance implementation - has bubble cycles

`default_nettype none

`timescale 1ns / 1ps

module axi_umi_bridge #(
    parameter integer ARWIDTH=32,
    parameter integer RWIDTH=32,
    parameter integer AWWIDTH=32,
    parameter integer WWIDTH=32
) (
    input clk,
    input rst,

    // AXI interface
    input axi_awvalid,
    output reg axi_awready = 1'b0,
    input [(AWWIDTH-1):0] axi_awaddr,
    input axi_wvalid,
    output reg axi_wready = 1'b0,
    input [(WWIDTH-1):0] axi_wdata,
    input [((WWIDTH/8)-1):0] axi_wstrb,
    output reg axi_bvalid = 1'b0,
    input axi_bready,
    input axi_arvalid,
    output reg axi_arready = 1'b0,
    input [(ARWIDTH-1):0] axi_araddr,
    output reg axi_rvalid = 1'b0,
    input axi_rready,
    output reg [(RWIDTH-1):0] axi_rdata = '0,

    // UMI outbound interface
    output reg [255:0] umi_out_packet = '0,
    output reg umi_out_valid = 1'b0,
    input umi_out_ready,

    // UMI inbound interface
    input [255:0] umi_in_packet,
    input umi_in_valid,
    output reg umi_in_ready = 1'b0
);

    `include "umi_messages.vh"

    // TODO: figure out how to deal with WSTRB
    // TODO: check dstaddr?

    // form UMI write packet

    /* verilator lint_off WIDTH */
    localparam [3:0] UMI_SIZE_WR = $clog2(WWIDTH/8);
    /* verilator lint_on WIDTH */

    wire [255:0] umi_write_packet;

    umi_pack umi_pack_wr (
        .write(WRITE_POSTED[0]),
        .command(WRITE_POSTED[7:1]),
        .size(UMI_SIZE_WR),
        .options(20'd0),
        .burst(1'b0),
        .dstaddr({{(64-AWWIDTH){1'b0}}, axi_awaddr}),
        .srcaddr(64'b0),  // only relevant for reads...
        .data({{(256-WWIDTH){1'b0}}, axi_wdata}),
        .packet(umi_write_packet)
    );

    // form UMI read packet

    /* verilator lint_off WIDTH */
    localparam [3:0] UMI_SIZE_RD = $clog2(RWIDTH/8);
    /* verilator lint_off WIDTH */

    wire [255:0] umi_read_packet;

    umi_pack umi_pack_rd (
        .write(READ_REQUEST[0]),
        .command(READ_REQUEST[7:1]),
        .size(UMI_SIZE_RD),
        .options(20'd0),
        .burst(1'b0),
        .dstaddr({{(64-ARWIDTH){1'b0}}, axi_araddr}),
        .srcaddr({{(64-ARWIDTH){1'b0}}, axi_araddr}),
        .data(256'b0),  // only relevant for writes...
        .packet(umi_read_packet)
    );

    // can only receive a response to data written

    wire [255:0] umi_in_data;
    wire [63:0] umi_in_dstaddr;
    wire [7:0] umi_in_opcode;

    assign umi_in_opcode = umi_in_packet[7:0];

    umi_unpack umi_unpack_i (
        // unpack data
        .packet(umi_in_packet),
        .data(umi_in_data),
        .dstaddr(umi_in_dstaddr),

        // unused outputs
        .write(),
        .command(),
        .size(),
        .options(),
        .srcaddr()
    );

    // main logic

    reg umi_read_in_progress = 1'b0;
    reg [63:0] expected_read_addr = '0;

    always @(posedge clk) begin
        if (rst) begin
            // TODO
        end else begin
            // handshaking
            // TODO: improve performance by removing bubble cycles

            if (axi_awvalid && axi_awready) begin
                axi_awready <= 1'b0;
            end

            if (axi_wvalid && axi_wready) begin
                axi_wready <= 1'b0;
            end

            if (axi_arvalid && axi_arready) begin
                axi_arready <= 1'b0;
            end

            if (axi_rvalid && axi_rready) begin
                axi_rvalid <= 1'b0;
                umi_read_in_progress <= 1'b0;
            end

            if (axi_bvalid && axi_bready) begin
                axi_bvalid <= 1'b0;
            end

            if (umi_out_valid && umi_out_ready) begin
                umi_out_valid <= 1'b0;
            end

            if (umi_in_valid && umi_in_ready) begin
                umi_in_ready <= 1'b0;
            end

            // deal with transmitting packets
            if (!umi_out_valid) begin
                if (axi_awvalid && (!axi_awready) && axi_wvalid && (!axi_wready) && (!axi_bvalid)) begin
                    // first see if there is data to be written (takes priority over read)
                    // this can happen if the address and data are valid, as long as we're
                    // not still trying to send the write response

                    // drive outbound packet
                    umi_out_packet <= umi_write_packet;
                    umi_out_valid <= 1'b1;

                    // handshaking
                    axi_awready <= 1'b1;
                    axi_wready <= 1'b1;
                    axi_bvalid <= 1'b1;
                end else if ((!umi_read_in_progress) && axi_arvalid && (!axi_arready)) begin
                    // if there isn't any data to be written, and we're not waiting for read
                    // data to come back, send out a read request if the read address is valid

                    // drive inbound packet
                    umi_out_packet <= umi_read_packet;
                    umi_out_valid <= 1'b1;
                    umi_read_in_progress <= 1'b1;
                    expected_read_addr <= {{(64-ARWIDTH){1'b0}}, axi_araddr};

                    // handshaking
                    axi_arready <= 1'b1;
                end
            end

            // deal with receiving packets
            if (umi_in_valid) begin
                // check that the packet makes sense
                if (!umi_read_in_progress) begin
                    $display("ERROR: received read response, but not waiting for a read to complete.");
                    $stop;
                end
                if (umi_in_dstaddr != expected_read_addr) begin
                    $display("ERROR: read response sent to the wrong address: got 0x%016x, expected 0x%016x",
                        umi_in_dstaddr, expected_read_addr);
                    $stop;
                end
                if (umi_in_opcode != WRITE_RESPONSE) begin
                    $display("ERROR: read response has wrong opcode: got 0x%02x, expected 0x%02x",
                        umi_in_opcode, WRITE_RESPONSE);
                    $stop;
                end

                if ((!axi_rvalid) && (!umi_in_ready)) begin
                    // if we're not currently driving read data, and we're not currently
                    // acknowledging receipt of a previous UMI packet, then we can drive
                    // the new data out and acknowledge receipt of this packet
                    axi_rdata <= umi_in_data[(RWIDTH-1):0];
                    axi_rvalid <= 1'b1;
                    umi_in_ready <= 1'b1;
                end
            end
        end
    end

endmodule
