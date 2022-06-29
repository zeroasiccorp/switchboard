// This is free and unencumbered software released into the public domain.
//
// Anyone is free to copy, modify, publish, use, compile, sell, or
// distribute this software, either in source code form or as a compiled
// binary, for any purpose, commercial or non-commercial, and by any
// means.

`resetall
`timescale 1ns / 1ps
`default_nettype none

module zverif_top (
	input clk,
	output trap,
	output trace_valid,
	output [35:0] trace_data,

	// outward-facing AXI RAM signals
	input [31:0] ext_awaddr,
	input ext_awvalid,
	output ext_awready,
	input [31:0] ext_wdata,
	input ext_wvalid,
	output ext_wready,
	input ext_bready,
	output ext_bvalid,

	// outward-facing AXI I/O signals
	output ctrl_awvalid,
	input ctrl_awready,
	output ctrl_wvalid,
	input ctrl_wready,
	input ctrl_bvalid,
	output ctrl_bready,
	output [31:0] ctrl_awaddr,
	output [31:0] ctrl_wdata
);
	// AXI reset
	reg axi_rst = 1;
	reg [3:0] axi_rst_count = 0;
	always @(posedge clk) begin
		if (axi_rst_count == '1) begin
			axi_rst <= 0;
			axi_rst_count <= axi_rst_count;
		end else begin
			axi_rst <= axi_rst;
			axi_rst_count <= axi_rst_count + 1;
		end
	end

	// CPU AXI interface

	wire        mem_axi_awvalid;
	wire        mem_axi_awready;
	wire [31:0] mem_axi_awaddr;
	wire [ 2:0] mem_axi_awprot;

	wire        mem_axi_wvalid;
	wire        mem_axi_wready;
	wire [31:0] mem_axi_wdata;
	wire [ 3:0] mem_axi_wstrb;

	wire        mem_axi_bvalid;
	wire        mem_axi_bready;

	wire        mem_axi_arvalid;
	wire        mem_axi_arready;
	wire [31:0] mem_axi_araddr;
	wire [ 2:0] mem_axi_arprot;

	wire        mem_axi_rvalid;
	wire        mem_axi_rready;
	wire [31:0] mem_axi_rdata;

	// RAM AXI signals

	wire [31:0] s_axil_a_awaddr;
	wire [2:0] s_axil_a_awprot;
	wire s_axil_a_awvalid;
	wire s_axil_a_awready;
	wire [31:0] s_axil_a_wdata;
	wire [3:0] s_axil_a_wstrb;
	wire s_axil_a_wvalid;
	wire s_axil_a_wready;
	wire [1:0] s_axil_a_bresp;
	wire s_axil_a_bvalid;
	wire s_axil_a_bready;
	wire [31:0] s_axil_a_araddr;
	wire [2:0] s_axil_a_arprot;
	wire s_axil_a_arvalid;
	wire s_axil_a_arready;
	wire [31:0] s_axil_a_rdata;
	wire [1:0] s_axil_a_rresp;
	wire s_axil_a_rvalid;
	wire s_axil_a_rready;

	wire [31:0] s_axil_b_awaddr;
	wire [2:0] s_axil_b_awprot;
	wire s_axil_b_awvalid;
	wire s_axil_b_awready;
	wire [31:0] s_axil_b_wdata;
	wire [3:0] s_axil_b_wstrb;
	wire s_axil_b_wvalid;
	wire s_axil_b_wready;
	wire [1:0] s_axil_b_bresp;
	wire s_axil_b_bvalid;
	wire s_axil_b_bready;
	wire [31:0] s_axil_b_araddr;
	wire [2:0] s_axil_b_arprot;
	wire s_axil_b_arvalid;
	wire s_axil_b_arready;
	wire [31:0] s_axil_b_rdata;
	wire [1:0] s_axil_b_rresp;
	wire s_axil_b_rvalid;
	wire s_axil_b_rready;

	wire gpio_awvalid;
	reg gpio_awready;
	wire [31:0] gpio_wdata;
	wire gpio_wvalid;
	reg gpio_wready;
	reg gpio_bvalid;
	wire gpio_bready;

	axil_interconnect_wrap_1x2 # (
		.DATA_WIDTH(32),
		.ADDR_WIDTH(32),
		.M00_BASE_ADDR(0), // RAM
		.M00_ADDR_WIDTH(32'd17),
		.M01_BASE_ADDR(32'h10000000), // External
		.M01_ADDR_WIDTH(32'd4),
		.M01_CONNECT_READ(1'b0)
	) iconnect_cpu (
		.clk(clk),
    	.rst(axi_rst),
    	.s00_axil_awaddr(mem_axi_awaddr),
    	.s00_axil_awprot(mem_axi_awprot),
    	.s00_axil_awvalid(mem_axi_awvalid),
    	.s00_axil_awready(mem_axi_awready),
    	.s00_axil_wdata(mem_axi_wdata),
    	.s00_axil_wstrb(mem_axi_wstrb),
    	.s00_axil_wvalid(mem_axi_wvalid),
    	.s00_axil_wready(mem_axi_wready),
    	.s00_axil_bresp(), // unused
    	.s00_axil_bvalid(mem_axi_bvalid),
    	.s00_axil_bready(mem_axi_bready),
    	.s00_axil_araddr(mem_axi_araddr),
    	.s00_axil_arprot(mem_axi_arprot),
    	.s00_axil_arvalid(mem_axi_arvalid),
    	.s00_axil_arready(mem_axi_arready),
    	.s00_axil_rdata(mem_axi_rdata),
    	.s00_axil_rresp(), // unused
    	.s00_axil_rvalid(mem_axi_rvalid),
    	.s00_axil_rready(mem_axi_rready),

		// RAM
		.m00_axil_awaddr(s_axil_a_awaddr),
    	.m00_axil_awprot(s_axil_a_awprot),
		.m00_axil_awvalid(s_axil_a_awvalid),
    	.m00_axil_awready(s_axil_a_awready),
    	.m00_axil_wdata(s_axil_a_wdata),
    	.m00_axil_wstrb(s_axil_a_wstrb),
    	.m00_axil_wvalid(s_axil_a_wvalid),
    	.m00_axil_wready(s_axil_a_wready),
    	.m00_axil_bresp(s_axil_a_bresp),
    	.m00_axil_bvalid(s_axil_a_bvalid),
    	.m00_axil_bready(s_axil_a_bready),
    	.m00_axil_araddr(s_axil_a_araddr),
    	.m00_axil_arprot(s_axil_a_arprot),
    	.m00_axil_arvalid(s_axil_a_arvalid),
    	.m00_axil_arready(s_axil_a_arready),
    	.m00_axil_rdata(s_axil_a_rdata),
    	.m00_axil_rresp(s_axil_a_rresp),
    	.m00_axil_rvalid(s_axil_a_rvalid),
    	.m00_axil_rready(s_axil_a_rready),

		// Writes to the outside
		.m01_axil_awaddr(ctrl_awaddr),
		.m01_axil_awprot(),  // unused
		.m01_axil_awvalid(ctrl_awvalid),
		.m01_axil_awready(ctrl_awready),
		.m01_axil_wdata(ctrl_wdata),
		.m01_axil_wstrb(),  // unused
		.m01_axil_wvalid(ctrl_wvalid),
		.m01_axil_wready(ctrl_wready),
		.m01_axil_bresp(2'b00),  // "OK"
		.m01_axil_bvalid(ctrl_bvalid),
		.m01_axil_bready(ctrl_bready),
		.m01_axil_araddr(),
		.m01_axil_arprot(),
		.m01_axil_arvalid(),
		.m01_axil_arready(1'b0),
		.m01_axil_rdata('0),
		.m01_axil_rresp(2'b00),
		.m01_axil_rvalid(1'b0),
		.m01_axil_rready()
	);

	axil_interconnect_wrap_1x2 # (
		.DATA_WIDTH(32),
		.ADDR_WIDTH(32),
		.M00_BASE_ADDR(0), // RAM
		.M00_ADDR_WIDTH(32'd17),
		.M01_BASE_ADDR(32'h20000000), // GPIO
		.M01_ADDR_WIDTH(32'd1),
		.M01_CONNECT_READ(1'b0)
	) iconnect_ext (
		.clk(clk),
    	.rst(axi_rst),

		// RAM
    	.s00_axil_awaddr(ext_awaddr),
    	.s00_axil_awprot(3'b000),
    	.s00_axil_awvalid(ext_awvalid),
    	.s00_axil_awready(ext_awready),
    	.s00_axil_wdata(ext_wdata),
    	.s00_axil_wstrb('1),
    	.s00_axil_wvalid(ext_wvalid),
    	.s00_axil_wready(ext_wready),
    	.s00_axil_bresp(), // unused
    	.s00_axil_bvalid(ext_bvalid),
    	.s00_axil_bready(ext_bready),
    	.s00_axil_araddr('0),
    	.s00_axil_arprot(3'b000),
    	.s00_axil_arvalid(1'b0),
    	.s00_axil_arready(),
    	.s00_axil_rdata(), // unused
    	.s00_axil_rresp(), // unused
    	.s00_axil_rvalid(), // unused
    	.s00_axil_rready(1'b0),

		// RAM
		.m00_axil_awaddr(s_axil_b_awaddr),
    	.m00_axil_awprot(s_axil_b_awprot),
		.m00_axil_awvalid(s_axil_b_awvalid),
    	.m00_axil_awready(s_axil_b_awready),
    	.m00_axil_wdata(s_axil_b_wdata),
    	.m00_axil_wstrb(s_axil_b_wstrb),
    	.m00_axil_wvalid(s_axil_b_wvalid),
    	.m00_axil_wready(s_axil_b_wready),
    	.m00_axil_bresp(s_axil_b_bresp),
    	.m00_axil_bvalid(s_axil_b_bvalid),
    	.m00_axil_bready(s_axil_b_bready),
    	.m00_axil_araddr(s_axil_b_araddr),
    	.m00_axil_arprot(s_axil_b_arprot),
    	.m00_axil_arvalid(s_axil_b_arvalid),
    	.m00_axil_arready(s_axil_b_arready),
    	.m00_axil_rdata(s_axil_b_rdata),
    	.m00_axil_rresp(s_axil_b_rresp),
    	.m00_axil_rvalid(s_axil_b_rvalid),
    	.m00_axil_rready(s_axil_b_rready),

		// GPIO
		.m01_axil_awaddr(), // unused
		.m01_axil_awprot(),  // unused
		.m01_axil_awvalid(gpio_awvalid),
		.m01_axil_awready(gpio_awready),
		.m01_axil_wdata(gpio_wdata),
		.m01_axil_wstrb(),  // unused
		.m01_axil_wvalid(gpio_wvalid),
		.m01_axil_wready(gpio_wready),
		.m01_axil_bresp(2'b00),  // "OK"
		.m01_axil_bvalid(gpio_bvalid),
		.m01_axil_bready(gpio_bready),
		.m01_axil_araddr(),
		.m01_axil_arprot(),
		.m01_axil_arvalid(),
		.m01_axil_arready(1'b0),
		.m01_axil_rdata('0),
		.m01_axil_rresp(2'b00),
		.m01_axil_rvalid(1'b0),
		.m01_axil_rready()
	);

	axil_dp_ram #(
		.DATA_WIDTH(32),
    	.ADDR_WIDTH(17),
	) ram (
		// interconnect-facing
		.a_clk(clk),
		.a_rst(axi_rst),
		.s_axil_a_awaddr(s_axil_a_awaddr[16:0]),
		.s_axil_a_awprot(s_axil_a_awprot),
		.s_axil_a_awvalid(s_axil_a_awvalid),
		.s_axil_a_awready(s_axil_a_awready),
		.s_axil_a_wdata(s_axil_a_wdata),
		.s_axil_a_wstrb(s_axil_a_wstrb),
		.s_axil_a_wvalid(s_axil_a_wvalid),
		.s_axil_a_wready(s_axil_a_wready),
		.s_axil_a_bresp(s_axil_a_bresp),
		.s_axil_a_bvalid(s_axil_a_bvalid),
		.s_axil_a_bready(s_axil_a_bready),
		.s_axil_a_araddr(s_axil_a_araddr[16:0]),
		.s_axil_a_arprot(s_axil_a_arprot),
		.s_axil_a_arvalid(s_axil_a_arvalid),
		.s_axil_a_arready(s_axil_a_arready),
		.s_axil_a_rdata(s_axil_a_rdata),
		.s_axil_a_rresp(s_axil_a_rresp),
		.s_axil_a_rvalid(s_axil_a_rvalid),
		.s_axil_a_rready(s_axil_a_rready),

		// external-facing
		.b_clk(clk),
		.b_rst(axi_rst),
		.s_axil_b_awaddr(s_axil_b_awaddr[16:0]),
		.s_axil_b_awprot(s_axil_b_awprot),
		.s_axil_b_awvalid(s_axil_b_awvalid),
		.s_axil_b_awready(s_axil_b_awready),
		.s_axil_b_wdata(s_axil_b_wdata),
		.s_axil_b_wstrb(s_axil_b_wstrb),
		.s_axil_b_wvalid(s_axil_b_wvalid),
		.s_axil_b_wready(s_axil_b_wready),
		.s_axil_b_bresp(s_axil_b_bresp),
		.s_axil_b_bvalid(s_axil_b_bvalid),
		.s_axil_b_bready(s_axil_b_bready),
		.s_axil_b_araddr(s_axil_b_araddr[16:0]),
		.s_axil_b_arprot(s_axil_b_arprot),
		.s_axil_b_arvalid(s_axil_b_arvalid),
		.s_axil_b_arready(s_axil_b_arready),
		.s_axil_b_rdata(s_axil_b_rdata),
		.s_axil_b_rresp(s_axil_b_rresp),
		.s_axil_b_rvalid(s_axil_b_rvalid),
		.s_axil_b_rready(s_axil_b_rready)
	);

	reg [31:0] gpio = 0;
	wire resetn;
	assign resetn = gpio[0];

	picorv32_axi #(
		.ENABLE_MUL(1),
		.ENABLE_DIV(1),
		.ENABLE_IRQ(1),
		.ENABLE_TRACE(1),
		.COMPRESSED_ISA(1)
	) uut (
		.clk            (clk            ),
		.resetn         (resetn         ),
		.trap           (trap           ),
		.mem_axi_awvalid(mem_axi_awvalid),
		.mem_axi_awready(mem_axi_awready),
		.mem_axi_awaddr (mem_axi_awaddr ),
		.mem_axi_awprot (mem_axi_awprot ),
		.mem_axi_wvalid (mem_axi_wvalid ),
		.mem_axi_wready (mem_axi_wready ),
		.mem_axi_wdata  (mem_axi_wdata  ),
		.mem_axi_wstrb  (mem_axi_wstrb  ),
		.mem_axi_bvalid (mem_axi_bvalid ),
		.mem_axi_bready (mem_axi_bready ),
		.mem_axi_arvalid(mem_axi_arvalid),
		.mem_axi_arready(mem_axi_arready),
		.mem_axi_araddr (mem_axi_araddr ),
		.mem_axi_arprot (mem_axi_arprot ),
		.mem_axi_rvalid (mem_axi_rvalid ),
		.mem_axi_rready (mem_axi_rready ),
		.mem_axi_rdata  (mem_axi_rdata  ),
		.irq            ('0             ),
		.trace_valid    (trace_valid    ),
		.trace_data     (trace_data     ),
		// unused pins
		.pcpi_insn(),
		.pcpi_rs1(),
		.pcpi_rs2(),
		.pcpi_wr(),
		.pcpi_rd(),
		.pcpi_wait(),
		.pcpi_ready(),
		.pcpi_valid(),
		.eoi()
	);

	// simple GPIO device

	always @(posedge clk) begin
		if (gpio_awvalid && gpio_wvalid &&
			((!gpio_awready) && (!gpio_wready)) &&
			((!gpio_bvalid) || gpio_bready)) begin
			gpio <= gpio_wdata;
			gpio_awready <= 1'b1;
			gpio_wready <= 1'b1;
			gpio_bvalid <= 1'b1;
		end else begin
			gpio_awready <= 1'b0;
			gpio_wready <= 1'b0;
			gpio_bvalid <= gpio_bvalid & (~gpio_bready);
			gpio <= gpio;
		end
	end

	// stop if there is a trap condition
	always @(posedge clk) begin
		if (resetn && trap) begin
			$display("TRAP");
			$stop;
		end
	end

endmodule

`resetall