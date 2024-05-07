// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module umi_fpga_queues #(
    parameter NUM_RX_QUEUES = 1,
    parameter NUM_TX_QUEUES = 1,
    parameter NUM_USER_REGS = 1,

    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32
) (
    input wire clk,
    input wire nreset,

    // UMI interfaces
    output wire [NUM_RX_QUEUES*DW-1:0] rx_data,
    output wire [NUM_RX_QUEUES*AW-1:0] rx_srcaddr,
    output wire [NUM_RX_QUEUES*AW-1:0] rx_dstaddr,
    output wire [NUM_RX_QUEUES*CW-1:0] rx_cmd,
    input wire [NUM_RX_QUEUES-1:0] rx_ready,
    output wire [NUM_RX_QUEUES-1:0] rx_valid,

    input wire [NUM_TX_QUEUES*DW-1:0] tx_data,
    input wire [NUM_TX_QUEUES*AW-1:0] tx_srcaddr,
    input wire [NUM_TX_QUEUES*AW-1:0] tx_dstaddr,
    input wire [NUM_TX_QUEUES*CW-1:0] tx_cmd,
    output wire [NUM_TX_QUEUES-1:0] tx_ready,
    input wire [NUM_TX_QUEUES-1:0] tx_valid,

    output wire [(NUM_USER_REGS > 0 ? NUM_USER_REGS : 1)*32-1:0] cfg_user,

    // AXI manager interface for memory access
    output wire [15:0] m_axi_awid,
    output wire [63:0] m_axi_awaddr,
    output wire [7:0] m_axi_awlen,
    output wire [2:0] m_axi_awsize,
    output wire [18:0] m_axi_awuser,
    output wire m_axi_awvalid,
    input wire m_axi_awready,

    output wire [511:0] m_axi_wdata,
    output wire [63:0] m_axi_wstrb,
    output wire m_axi_wlast,
    output wire m_axi_wvalid,
    input wire m_axi_wready,

    input wire [15:0] m_axi_bid,
    input wire [1:0] m_axi_bresp,
    input wire m_axi_bvalid,
    output wire m_axi_bready,

    output wire [15:0] m_axi_arid,
    output wire [63:0] m_axi_araddr,
    output wire [7:0] m_axi_arlen,
    output wire [2:0] m_axi_arsize,
    output wire [18:0] m_axi_aruser,
    output wire m_axi_arvalid,
    input wire m_axi_arready,

    input wire [15:0] m_axi_rid,
    input wire [511:0] m_axi_rdata,
    input wire [1:0] m_axi_rresp,
    input wire m_axi_rlast,
    input wire m_axi_rvalid,
    output wire m_axi_rready,

    // AXIL subordinate interface for config registers
    input wire s_axil_awvalid,
    input wire [31:0] s_axil_awaddr,
    output wire s_axil_awready,

    input wire s_axil_wvalid,
    input wire [31:0] s_axil_wdata,
    input wire [3:0] s_axil_wstrb,
    output wire s_axil_wready,

    output wire s_axil_bvalid,
    output wire [1:0] s_axil_bresp,
    input wire s_axil_bready,

    input wire s_axil_arvalid,
    input wire [31:0] s_axil_araddr,
    output wire s_axil_arready,

    output wire s_axil_rvalid,
    output wire [31:0] s_axil_rdata,
    output wire [1:0] s_axil_rresp,
    input wire s_axil_rready
);

    localparam SB_DW = DW + AW + AW + CW;

    // Pack/unpack UMI signals to/from Switchboard packets

    genvar i;
    wire [NUM_RX_QUEUES*SB_DW-1:0] sb_rx_data;
    for (i = 0; i < NUM_RX_QUEUES; i = i + 1) begin
        assign rx_cmd[i*CW+:CW] = sb_rx_data[i*SB_DW + CW-1:i*SB_DW];
        assign rx_dstaddr[i*AW+:AW] = sb_rx_data[i*SB_DW + AW+CW-1:i*SB_DW + CW];
        assign rx_srcaddr[i*AW+:AW] = sb_rx_data[i*SB_DW + AW+AW+CW-1:i*SB_DW + AW+CW];
        assign rx_data[i*DW+:DW] = sb_rx_data[i*SB_DW + DW+AW+AW+CW-1:i*SB_DW + AW+AW+CW];
    end

    wire [NUM_TX_QUEUES*SB_DW-1:0] sb_tx_data;
    wire [NUM_TX_QUEUES*32-1:0] sb_tx_dest;
    wire [NUM_TX_QUEUES-1:0] sb_tx_last;
    for (i = 0; i < NUM_TX_QUEUES; i = i + 1) begin
        assign sb_tx_data[i*SB_DW+:SB_DW] = {
            tx_data[i*DW+:DW], tx_srcaddr[i*AW+:AW], tx_dstaddr[i*AW+:AW], tx_cmd[i*CW+:CW]
        };
        assign sb_tx_dest[i*32+:32] = {16'h0000, tx_dstaddr[i*AW+55:i*AW+40]};
        assign sb_tx_last[i] = tx_cmd[(i*CW)+22];
    end

    sb_fpga_queues #(
        .NUM_RX_QUEUES(NUM_RX_QUEUES),
        .NUM_TX_QUEUES(NUM_TX_QUEUES),
        .NUM_USER_REGS(NUM_USER_REGS),

        .DW(SB_DW)
    ) sb_fpga_queues_i (
        .clk(clk),
        .nreset(nreset),

        .rx_data(sb_rx_data),
        .rx_dest(),
        .rx_last(),
        .rx_ready(rx_ready),
        .rx_valid(rx_valid),

        .tx_data(sb_tx_data),
        .tx_dest(sb_tx_dest),
        .tx_last(sb_tx_last),
        .tx_ready(tx_ready),
        .tx_valid(tx_valid),

        // Pass thru AXI ports implicitly
        .*
    );

endmodule

`default_nettype wire
