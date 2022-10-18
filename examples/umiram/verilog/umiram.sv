`include "umi_opcodes.vh"

module umiram #(
    parameter integer ADDR_WIDTH=8,
    parameter integer DATA_WIDTH=32
) (
	input clk,
	input [255:0] umi_rx_packet,
	input umi_rx_valid,
	output reg umi_rx_ready=1'b0,
	output [255:0] umi_tx_packet,
	output reg umi_tx_valid=1'b0,
	input umi_tx_ready
);
    // interpret incoming packet

    wire [31:0] rx_cmd;
    wire rx_cmd_read;
    wire rx_cmd_write;
    wire [63:0] rx_dstaddr;
    wire [63:0] rx_srcaddr;
    wire [255:0] rx_data;

	umi_unpack umi_unpack_i (
        // input
    	.packet(umi_rx_packet),

        // output
        .data(rx_data),
        .srcaddr(rx_srcaddr),
        .dstaddr(rx_dstaddr),
		.cmd(rx_cmd)
    );

    /* verilator lint_off PINMISSING */
    umi_decode umi_decode_i (
        .cmd(rx_cmd),
        .cmd_read(rx_cmd_read),
        .cmd_write(rx_cmd_write)
    );
    /* verilator lint_on PINMISSING */

    // form outgoing packet (which can only be a read response)

    reg [63:0] tx_dstaddr;
    reg [255:0] tx_data;

    /* verilator lint_off WIDTH */
    localparam [3:0] UMI_SIZE = $clog2(DATA_WIDTH/8);
    /* verilator lint_on WIDTH */

	umi_pack umi_pack_i (
		.opcode(`UMI_WRITE_RESPONSE),  // WRITE-NORMAL
		.size(UMI_SIZE),
		.user(20'd0),
		.burst(1'b0),
		.dstaddr(tx_dstaddr),
		.srcaddr(64'd0),
		.data(tx_data),
		.packet(umi_tx_packet)
	);

    // main logic

    reg [(DATA_WIDTH-1):0] mem[2**ADDR_WIDTH];

    always @(posedge clk) begin
        // handle receiver
        if (umi_rx_valid && umi_rx_ready) begin
            umi_rx_ready <= 1'b0;
        end else if (umi_rx_valid) begin
            if (rx_cmd_write) begin
                mem[rx_dstaddr[(ADDR_WIDTH-1):0]] <= rx_data[(DATA_WIDTH-1):0];
                umi_rx_ready <= 1'b1;
            end else if (rx_cmd_read && !umi_tx_valid) begin
                tx_data <= {{(256-DATA_WIDTH){1'b0}}, mem[rx_dstaddr[(ADDR_WIDTH-1):0]]};
                tx_dstaddr <= rx_srcaddr;
                umi_tx_valid <= 1'b1;
                umi_rx_ready <= 1'b1;
            end
        end

        // handle transmitter
        if (umi_tx_valid && umi_tx_ready) begin
            umi_tx_valid <= 1'b0;
        end
    end

endmodule
