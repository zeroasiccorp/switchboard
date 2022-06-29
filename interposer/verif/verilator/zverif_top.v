// This is free and unencumbered software released into the public domain.
//
// Anyone is free to copy, modify, publish, use, compile, sell, or
// distribute this software, either in source code form or as a compiled
// binary, for any purpose, commercial or non-commercial, and by any
// means.

`timescale 1 ns / 1 ps

module zverif_top (
	input clk,
	input resetn,
	output trap,
	output trace_valid,
	output [35:0] trace_data,

	// outward-facing AXI RAM signals
	input axi_rst,
	input [16:0] ext_awaddr,
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

	wire mem_axi_awaddr_int;
	assign mem_axi_awaddr_int = (mem_axi_awaddr <= 17'h1FFFF);

	wire s_axil_a_awready;
	assign mem_axi_awready = mem_axi_awaddr_int ? s_axil_a_awready : ctrl_awready;
	
	wire s_axil_a_wready;
	assign mem_axi_wready = mem_axi_awaddr_int ? s_axil_a_wready : ctrl_wready;

	wire s_axil_a_bvalid;
	assign mem_axi_bvalid = mem_axi_awaddr_int ? s_axil_a_bvalid : ctrl_bvalid;	

	axil_dp_ram #(
		.DATA_WIDTH(32),
    	.ADDR_WIDTH(17),
	) ram (
		.a_clk(clk),
		.a_rst(axi_rst),

		.b_clk(clk),
		.b_rst(axi_rst),

		.s_axil_a_awaddr(mem_axi_awaddr[16:0]),
		.s_axil_a_awprot(mem_axi_awprot),
		.s_axil_a_awvalid(mem_axi_awvalid & mem_axi_awaddr_int),
		.s_axil_a_awready(s_axil_a_awready),
		.s_axil_a_wdata(mem_axi_wdata),
		.s_axil_a_wstrb(mem_axi_wstrb),
		.s_axil_a_wvalid(mem_axi_wvalid & mem_axi_awaddr_int),
		.s_axil_a_wready(s_axil_a_wready),
		.s_axil_a_bresp(),
		.s_axil_a_bvalid(s_axil_a_bvalid),
		.s_axil_a_bready(mem_axi_bready),
		.s_axil_a_araddr(mem_axi_araddr[16:0]),
		.s_axil_a_arprot(mem_axi_arprot),
		.s_axil_a_arvalid(mem_axi_arvalid),
		.s_axil_a_arready(mem_axi_arready),

		.s_axil_a_rdata(mem_axi_rdata),
		.s_axil_a_rresp(),
		.s_axil_a_rvalid(mem_axi_rvalid),
		.s_axil_a_rready(mem_axi_rready),

		.s_axil_b_awaddr(ext_awaddr),
		.s_axil_b_awprot('0),
		.s_axil_b_awvalid(ext_awvalid),
		.s_axil_b_awready(ext_awready),
		.s_axil_b_wdata(ext_wdata),
		.s_axil_b_wstrb('1),
		.s_axil_b_wvalid(ext_wvalid),
		.s_axil_b_wready(ext_wready),
		.s_axil_b_bresp(),
		.s_axil_b_bvalid(ext_bvalid),
		.s_axil_b_bready(ext_bready),
		.s_axil_b_araddr('0),
		.s_axil_b_arprot('0),
		.s_axil_b_arvalid('0),
		.s_axil_b_arready(),
		.s_axil_b_rdata(),
		.s_axil_b_rresp(),
		.s_axil_b_rvalid(),
		.s_axil_b_rready(1'b0)
	);

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

	// drive control outputs
	assign ctrl_awvalid = (!mem_axi_awaddr_int) & mem_axi_awvalid;
	assign ctrl_wvalid = (!mem_axi_awaddr_int) & mem_axi_wvalid;
	assign ctrl_bready = mem_axi_bready;
	assign ctrl_awaddr = mem_axi_awaddr;
	assign ctrl_wdata = mem_axi_wdata;

	// stop if there is a trap condition
	always @(posedge clk) begin
		if (resetn && trap) begin
			$display("TRAP");
			$stop;
		end
	end

endmodule
