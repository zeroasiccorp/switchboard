// only handles writes
// not high performance - has bubble cycles

module umi_to_axi (
    input clk,
    input rst,
    // UMI interface
    input [255:0] umi_packet,
    input umi_valid,
    output umi_ready,
    // AXI interface
    output reg axi_awvalid,
    input axi_awready,
    output reg axi_wvalid,
    input axi_wready,
    input axi_bvalid,
    output reg axi_bready,
    output [63:0] axi_awaddr,
    output [255:0] axi_wdata
);

	reg in_progress;
	always @(posedge clk) begin
		if (rst) begin
            axi_awvalid <= 1'b0;
            axi_wvalid <= 1'b0;
            axi_bready <= 1'b0;
			in_progress <= 1'b0;
		end else if (in_progress) begin
			axi_awvalid <= axi_awvalid & (~axi_awready);
			axi_wvalid <= axi_wvalid & (~axi_wready);
			axi_bready <= axi_bvalid & (~axi_bready);
			if (!umi_valid) begin
				in_progress <= 1'b0;
			end
		end else if (umi_valid) begin
			axi_awvalid <= 1'b1;
			axi_wvalid <= 1'b1;
			axi_bready <= 1'b0;
			in_progress <= 1'b1;
		end
	end
	
	assign umi_ready = axi_bready;

	umi_unpack umi_unpack_i (
    	.packet(umi_packet),
        .dstaddr(axi_awaddr),
		.data(axi_wdata),

        // all of these outputs are unused...
        .srcaddr(),
		.cmd_write(),
		.cmd_read(),
		.cmd_atomic(),
		.cmd_write_normal(),
		.cmd_write_signal(),
		.cmd_write_ack(),
		.cmd_write_stream(),
		.cmd_write_response(),
		.cmd_atomic_swap(),
		.cmd_atomic_add(),
		.cmd_atomic_and(),
		.cmd_atomic_or(),
		.cmd_atomic_xor(),
		.cmd_atomic_min(),
		.cmd_invalid(),
		.cmd_atomic_max(),
		.cmd_opcode(),
    	.cmd_size(),
    	.cmd_user()
    );

endmodule
