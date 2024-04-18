// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_fpga_queues #(
    parameter NUM_RX_QUEUES = 1,
    parameter NUM_TX_QUEUES = 1,
    parameter NUM_USER_REGS = 0,

    parameter integer DW=416
) (
    input wire clk,
    input wire nreset,

    // Switchboard interfaces
    output wire [NUM_RX_QUEUES*DW-1:0] rx_data,
    output wire [NUM_RX_QUEUES*32-1:0] rx_dest,
    output wire [NUM_RX_QUEUES-1:0] rx_last,
    input wire [NUM_RX_QUEUES-1:0] rx_ready,
    output wire [NUM_RX_QUEUES-1:0] rx_valid,

    input wire [NUM_TX_QUEUES*DW-1:0] tx_data,
    input wire [NUM_TX_QUEUES*32-1:0] tx_dest,
    input wire [NUM_TX_QUEUES-1:0] tx_last,
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

    localparam NUM_QUEUES = NUM_RX_QUEUES + NUM_TX_QUEUES;
    // We have a fixed number of ID bits out, and we need to reserve a few for
    // response routing in the arbiter.
    localparam ID_WIDTH = 16 - $clog2(NUM_QUEUES);

    wire [NUM_QUEUES-1:0] cfg_enable;
    wire [NUM_QUEUES-1:0] cfg_reset;
    wire [NUM_QUEUES*64-1:0] cfg_base_addr;
    wire [NUM_QUEUES*32-1:0] cfg_capacity;

    wire [NUM_QUEUES-1:0] status_idle;

    wire [NUM_QUEUES*ID_WIDTH-1:0] axi_awid;
    wire [NUM_QUEUES*64-1:0] axi_awaddr;
    wire [NUM_QUEUES*8-1:0] axi_awlen;
    wire [NUM_QUEUES*3-1:0] axi_awsize;
    wire [NUM_QUEUES-1:0] axi_awvalid;
    wire [NUM_QUEUES-1:0] axi_awready;

    wire [NUM_QUEUES*512-1:0] axi_wdata;
    wire [NUM_QUEUES*64-1:0] axi_wstrb;
    wire [NUM_QUEUES-1:0] axi_wlast;
    wire [NUM_QUEUES-1:0] axi_wvalid;
    wire [NUM_QUEUES-1:0] axi_wready;

    wire [NUM_QUEUES*ID_WIDTH-1:0] axi_bid;
    wire [NUM_QUEUES*2-1:0] axi_bresp;
    wire [NUM_QUEUES-1:0] axi_bvalid;
    wire [NUM_QUEUES-1:0] axi_bready;

    wire [NUM_QUEUES*ID_WIDTH-1:0] axi_arid;
    wire [NUM_QUEUES*64-1:0] axi_araddr;
    wire [NUM_QUEUES*8-1:0] axi_arlen;
    wire [NUM_QUEUES*3-1:0] axi_arsize;
    wire [NUM_QUEUES-1:0] axi_arvalid;
    wire [NUM_QUEUES-1:0] axi_arready;

    wire [NUM_QUEUES*ID_WIDTH-1:0] axi_rid;
    wire [NUM_QUEUES*512-1:0] axi_rdata;
    wire [NUM_QUEUES*2-1:0] axi_rresp;
    wire [NUM_QUEUES-1:0] axi_rlast;
    wire [NUM_QUEUES-1:0] axi_rvalid;
    wire [NUM_QUEUES-1:0] axi_rready;

    genvar i;
    generate
        for (i = 0; i < NUM_RX_QUEUES; i = i + 1) begin
            sb_rx_fpga #(
                .ID_WIDTH(ID_WIDTH),
                .DW(DW)
            ) rx (
                .clk(clk),
                .en(cfg_enable[2*i]),
                .reset(cfg_reset[2*i]),

                .cfg_base_addr(cfg_base_addr[64*(2*i)+:64]),
                .cfg_capacity(cfg_capacity[32*(2*i)+:32]),

                .status_idle(status_idle[2*i]),

                .data(rx_data[DW*i+:DW]),
                .dest(rx_dest[32*i+:32]),
                .last(rx_last[i]),
                .ready(rx_ready[i]),
                .valid(rx_valid[i]),

                .m_axi_awid(axi_awid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_awaddr(axi_awaddr[64*i+:64]),
                .m_axi_awlen(axi_awlen[8*i+:8]),
                .m_axi_awsize(axi_awsize[3*i+:3]),
                .m_axi_awvalid(axi_awvalid[i]),
                .m_axi_awready(axi_awready[i]),

                .m_axi_wdata(axi_wdata[512*i+:512]),
                .m_axi_wstrb(axi_wstrb[64*i+:64]),
                .m_axi_wlast(axi_wlast[i]),
                .m_axi_wvalid(axi_wvalid[i]),
                .m_axi_wready(axi_wready[i]),

                .m_axi_bid(axi_bid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_bresp(axi_bresp[2*i+:2]),
                .m_axi_bvalid(axi_bvalid[i]),
                .m_axi_bready(axi_bready[i]),

                .m_axi_arid(axi_arid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_araddr(axi_araddr[64*i+:64]),
                .m_axi_arlen(axi_arlen[8*i+:8]),
                .m_axi_arsize(axi_arsize[3*i+:3]),
                .m_axi_arvalid(axi_arvalid[i]),
                .m_axi_arready(axi_arready[i]),

                .m_axi_rid(axi_rid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_rdata(axi_rdata[512*i+:512]),
                .m_axi_rresp(axi_rresp[2*i+:2]),
                .m_axi_rlast(axi_rlast[i]),
                .m_axi_rvalid(axi_rvalid[i]),
                .m_axi_rready(axi_rready[i])
            );
        end
    endgenerate

    generate
        for (i = NUM_RX_QUEUES; i < NUM_QUEUES; i = i + 1) begin
            sb_tx_fpga #(
                .ID_WIDTH(ID_WIDTH),
                .DW(DW)
            ) tx (
                .clk(clk),
                .en(cfg_enable[2*(i-NUM_RX_QUEUES)+1]),
                .reset(cfg_reset[2*(i-NUM_RX_QUEUES)+1]),

                .cfg_base_addr(cfg_base_addr[64*(2*(i-NUM_RX_QUEUES)+1)+:64]),
                .cfg_capacity(cfg_capacity[32*(2*(i-NUM_RX_QUEUES)+1)+:32]),

                .status_idle(status_idle[2*(i-NUM_RX_QUEUES)+1]),

                .data(tx_data[DW*(i-NUM_RX_QUEUES)+:DW]),
                .dest(tx_dest[32*(i-NUM_RX_QUEUES)+:32]),
                .last(tx_last[i-NUM_RX_QUEUES]),
                .ready(tx_ready[i-NUM_RX_QUEUES]),
                .valid(tx_valid[i-NUM_RX_QUEUES]),

                .m_axi_awid(axi_awid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_awaddr(axi_awaddr[64*i+:64]),
                .m_axi_awlen(axi_awlen[8*i+:8]),
                .m_axi_awsize(axi_awsize[3*i+:3]),
                .m_axi_awvalid(axi_awvalid[i]),
                .m_axi_awready(axi_awready[i]),

                .m_axi_wdata(axi_wdata[512*i+:512]),
                .m_axi_wstrb(axi_wstrb[64*i+:64]),
                .m_axi_wlast(axi_wlast[i]),
                .m_axi_wvalid(axi_wvalid[i]),
                .m_axi_wready(axi_wready[i]),

                .m_axi_bid(axi_bid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_bresp(axi_bresp[2*i+:2]),
                .m_axi_bvalid(axi_bvalid[i]),
                .m_axi_bready(axi_bready[i]),

                .m_axi_arid(axi_arid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_araddr(axi_araddr[64*i+:64]),
                .m_axi_arlen(axi_arlen[8*i+:8]),
                .m_axi_arsize(axi_arsize[3*i+:3]),
                .m_axi_arvalid(axi_arvalid[i]),
                .m_axi_arready(axi_arready[i]),

                .m_axi_rid(axi_rid[ID_WIDTH*i+:ID_WIDTH]),
                .m_axi_rdata(axi_rdata[512*i+:512]),
                .m_axi_rresp(axi_rresp[2*i+:2]),
                .m_axi_rlast(axi_rlast[i]),
                .m_axi_rvalid(axi_rvalid[i]),
                .m_axi_rready(axi_rready[i])
            );
        end
    endgenerate

    config_registers #(
        .NUM_QUEUES(NUM_QUEUES),
        .NUM_USER_REGS(NUM_USER_REGS)
    ) config_regs (
        .clk(clk),
        .nreset(nreset),

        .status_idle(status_idle),
        .cfg_enable(cfg_enable),
        .cfg_reset(cfg_reset),
        .cfg_base_addr(cfg_base_addr),
        .cfg_capacity(cfg_capacity),
        .cfg_user(cfg_user),

        .s_axil_awaddr(s_axil_awaddr),
        .s_axil_awvalid(s_axil_awvalid),
        .s_axil_awready(s_axil_awready),
        .s_axil_wdata(s_axil_wdata),
        .s_axil_wstrb(s_axil_wstrb),
        .s_axil_wvalid(s_axil_wvalid),
        .s_axil_wready(s_axil_wready),
        .s_axil_bresp(s_axil_bresp),
        .s_axil_bvalid(s_axil_bvalid),
        .s_axil_bready(s_axil_bready),
        .s_axil_araddr(s_axil_araddr),
        .s_axil_arvalid(s_axil_arvalid),
        .s_axil_arready(s_axil_arready),
        .s_axil_rdata(s_axil_rdata),
        .s_axil_rresp(s_axil_rresp),
        .s_axil_rvalid(s_axil_rvalid),
        .s_axil_rready(s_axil_rready)
    );

    // Handles arbitration between AXI interfaces on queues, as well as
    // registering outputs.
    axi_crossbar #(
        .S_COUNT(NUM_QUEUES),
        .M_COUNT(1),
        .DATA_WIDTH(512),
        .ADDR_WIDTH(64),
        .S_ID_WIDTH(ID_WIDTH),
        .M_ADDR_WIDTH(32'd64),
        .S_AW_REG_TYPE({NUM_QUEUES{2'd0}}),
        .S_W_REG_TYPE({NUM_QUEUES{2'd0}}),
        .S_B_REG_TYPE({NUM_QUEUES{2'd0}}),
        .S_AR_REG_TYPE({NUM_QUEUES{2'd0}}),
        .S_R_REG_TYPE({NUM_QUEUES{2'd0}}),
        .M_AW_REG_TYPE(2'd2),
        .M_W_REG_TYPE(2'd2),
        .M_B_REG_TYPE(2'd2),
        .M_AR_REG_TYPE(2'd2),
        .M_R_REG_TYPE(2'd2)
    ) crossbar (
        .clk(clk),
        .rst(~nreset),

        .s_axi_awid(axi_awid),
        .s_axi_awaddr(axi_awaddr),
        .s_axi_awlen(axi_awlen),
        .s_axi_awsize(axi_awsize),
        .s_axi_awburst(),
        .s_axi_awlock(),
        .s_axi_awcache(),
        .s_axi_awprot(),
        .s_axi_awqos(),
        .s_axi_awuser(),
        .s_axi_awvalid(axi_awvalid),
        .s_axi_awready(axi_awready),
        .s_axi_wdata(axi_wdata),
        .s_axi_wstrb(axi_wstrb),
        .s_axi_wlast(axi_wlast),
        .s_axi_wuser(),
        .s_axi_wvalid(axi_wvalid),
        .s_axi_wready(axi_wready),
        .s_axi_bid(axi_bid),
        .s_axi_bresp(axi_bresp),
        .s_axi_buser(),
        .s_axi_bvalid(axi_bvalid),
        .s_axi_bready(axi_bready),
        .s_axi_arid(axi_arid),
        .s_axi_araddr(axi_araddr),
        .s_axi_arlen(axi_arlen),
        .s_axi_arsize(axi_arsize),
        .s_axi_arburst(),
        .s_axi_arlock(),
        .s_axi_arcache(),
        .s_axi_arprot(),
        .s_axi_arqos(),
        .s_axi_aruser(),
        .s_axi_arvalid(axi_arvalid),
        .s_axi_arready(axi_arready),
        .s_axi_rid(axi_rid),
        .s_axi_rdata(axi_rdata),
        .s_axi_rresp(axi_rresp),
        .s_axi_rlast(axi_rlast),
        .s_axi_ruser(),
        .s_axi_rvalid(axi_rvalid),
        .s_axi_rready(axi_rready),

        .m_axi_awid     (m_axi_awid),
        .m_axi_awaddr   (m_axi_awaddr),
        .m_axi_awlen    (m_axi_awlen),
        .m_axi_awsize   (m_axi_awsize),
        .m_axi_awburst  (),
        .m_axi_awlock   (),
        .m_axi_awcache  (),
        .m_axi_awprot   (),
        .m_axi_awqos    (),
        .m_axi_awregion (),
        .m_axi_awuser   (),
        .m_axi_awvalid  (m_axi_awvalid),
        .m_axi_awready  (m_axi_awready),
        .m_axi_wdata    (m_axi_wdata),
        .m_axi_wstrb    (m_axi_wstrb),
        .m_axi_wlast    (m_axi_wlast),
        .m_axi_wuser    (),
        .m_axi_wvalid   (m_axi_wvalid),
        .m_axi_wready   (m_axi_wready),
        .m_axi_bid      (m_axi_bid),
        .m_axi_bresp    (m_axi_bresp),
        .m_axi_buser    (),
        .m_axi_bvalid   (m_axi_bvalid),
        .m_axi_bready   (m_axi_bready),
        .m_axi_arid     (m_axi_arid),
        .m_axi_araddr   (m_axi_araddr),
        .m_axi_arlen    (m_axi_arlen),
        .m_axi_arsize   (m_axi_arsize),
        .m_axi_arburst  (),
        .m_axi_arlock   (),
        .m_axi_arcache  (),
        .m_axi_arprot   (),
        .m_axi_arqos    (),
        .m_axi_arregion (),
        .m_axi_aruser   (),
        .m_axi_arvalid  (m_axi_arvalid),
        .m_axi_arready  (m_axi_arready),
        .m_axi_rid      (m_axi_rid),
        .m_axi_rdata    (m_axi_rdata),
        .m_axi_rresp    (m_axi_rresp),
        .m_axi_rlast    (m_axi_rlast),
        .m_axi_ruser    (),
        .m_axi_rvalid   (m_axi_rvalid),
        .m_axi_rready   (m_axi_rready)
    );

`ifdef DEBUG
    ila_0 ILA_PCIM_RD (
                .clk    (clk),
                .probe0 (m_axi_arvalid),
                .probe1 (m_axi_araddr),
                .probe2 (m_axi_arready),
                .probe3 (m_axi_rvalid),
                .probe4 (m_axi_rdata[63:0]),
                .probe5 (m_axi_rready)
                );

    ila_0 ILA_PCIM_WR (
                .clk    (clk),
                .probe0 (m_axi_awvalid),
                .probe1 (m_axi_awaddr),
                .probe2 (m_axi_awready),
                .probe3 (m_axi_wvalid),
                .probe4 (m_axi_wdata[63:0]),
                .probe5 (m_axi_wready)
                );
`endif

endmodule

`default_nettype wire
