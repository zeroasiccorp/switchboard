`timescale 1 ns / 1 ps

`default_nettype none

module loopback (
    input wire clk,
    input wire nreset,

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

    localparam NUM_RX_QUEUES = 1;
    localparam NUM_TX_QUEUES = 1;
    localparam NUM_QUEUES = NUM_RX_QUEUES + NUM_TX_QUEUES;

	// SB RX port
    wire [255:0] sb_rx_data;
	wire [31:0] sb_rx_dest;
	wire sb_rx_last;
	wire sb_rx_valid;
	wire sb_rx_ready;

	// SB TX port
	wire [255:0] sb_tx_data;
	wire [31:0] sb_tx_dest;
	wire sb_tx_last;
	wire sb_tx_valid;
	wire sb_tx_ready;

    sb_fpga_queues queues (
        .clk(clk),
        .nreset(nreset),

        .rx_data(sb_rx_data),
        .rx_dest(sb_rx_dest),
        .rx_last(sb_rx_last),
        .rx_ready(sb_rx_ready),
        .rx_valid(sb_rx_valid),

        .tx_data(sb_tx_data),
        .tx_dest(sb_tx_dest),
        .tx_last(sb_tx_last),
        .tx_ready(sb_tx_ready),
        .tx_valid(sb_tx_valid),

        .*
    );

	// custom modification of packet
	genvar i;
	generate
		for (i=0; i<32; i=i+1) begin
			assign sb_tx_data[(i*8) +: 8] = sb_rx_data[(i*8) +: 8] + 8'd1;
		end
	endgenerate

	assign sb_tx_dest = sb_rx_dest;
	assign sb_tx_last = sb_rx_last;
	assign sb_tx_valid = sb_rx_valid;
	assign sb_rx_ready = sb_tx_ready;

endmodule

`default_nettype wire
