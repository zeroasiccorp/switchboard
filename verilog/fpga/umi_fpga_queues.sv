module umi_fpga_queues #(
    parameter NUM_RX_QUEUES = 1,
    parameter NUM_TX_QUEUES = 1
) (
    input wire clk,
    input wire nreset,

    // UMI interfaces
    output wire [NUM_RX_QUEUES*256-1:0] rx_packet,
    input wire [NUM_RX_QUEUES-1:0] rx_ready,
    output wire [NUM_RX_QUEUES-1:0] rx_valid,

    input wire [NUM_TX_QUEUES*256-1:0] tx_packet,
    output wire [NUM_TX_QUEUES-1:0] tx_ready,
    input wire [NUM_TX_QUEUES-1:0] tx_valid,

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

    genvar i;
    wire [NUM_TX_QUEUES*32-1:0] tx_dest;

    for (i = 0; i < NUM_TX_QUEUES; i = i + 1) begin
        assign tx_dest[i*32+:32] = {16'h0000, tx_packet[256*(i+1)-1-:16]};
    end

    sb_fpga_queues #(
        .NUM_RX_QUEUES(NUM_RX_QUEUES),
        .NUM_TX_QUEUES(NUM_TX_QUEUES)
    ) sb_fpga_queues_i (
        .clk(clk),
        .nreset(nreset),

        .rx_data(rx_packet),
        .rx_dest(),
        .rx_last(),
        .rx_ready(rx_ready),
        .rx_valid(rx_valid),

        .tx_data(tx_packet),
        .tx_dest(tx_dest),
        // TODO: support burst mode
        .tx_last(3'b1),
        .tx_ready(tx_ready),
        .tx_valid(tx_valid),

        // Pass thru AXI ports implicitly
        .*
    );

endmodule
