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

        // unused outputs...
        .write(),
        .command(),
        .size(),
        .options(),
        .srcaddr()
    );

endmodule
