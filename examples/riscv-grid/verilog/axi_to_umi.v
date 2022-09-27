// only handles writes
// not high performance - has bubble cycles

`include "umi_opcodes.vh"

module axi_to_umi (
    input clk,
    input rst,
    // AXI interface
    input axi_awvalid,
    output axi_awready,
    input axi_wvalid,
    output axi_wready,
    output reg axi_bvalid,
    input axi_bready,
    input [63:0] axi_awaddr,
    input [255:0] axi_wdata,
    // UMI interface
    output [255:0] umi_packet,
    output umi_valid,
    input umi_ready
);

	// UMI packet is valid when both address
	// and data are valid.
	assign umi_valid = axi_awvalid & axi_awvalid;

	// both address and data use the same "ready"
	// signal, since they are sent as a packet
	assign axi_awready = umi_ready;
	assign axi_wready = umi_ready;

	// special handling for bvalid: need to keep this
	// asserted until acknolwedged with bready.  this might
	// not happen instantaneously, so state is needed to
	// keep track of whether bvalid should be asserted.
	always @(posedge clk) begin
		if (rst) begin
			axi_bvalid <= 1'b0;
		end else begin
			axi_bvalid <= umi_ready | (axi_bvalid & (~axi_bready));
		end
	end

	umi_pack umi_pack_i (
		.opcode(`UMI_WRITE_NORMAL),
		.size(4'd0),
		.user(20'd0),
		.burst(1'b0),
		.dstaddr(axi_awaddr),
		.srcaddr(64'd0),
		.data(axi_wdata),
		.packet(umi_packet)
	);

endmodule
