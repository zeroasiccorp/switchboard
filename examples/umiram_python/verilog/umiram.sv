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

    `include "umi_messages.vh"

    // interpret incoming packet

    wire [7:0] rx_opcode;
    wire rx_cmd_read;
    wire rx_cmd_write;
    wire [63:0] rx_dstaddr;
    wire [63:0] rx_srcaddr;
    wire [255:0] rx_data;

	umi_unpack umi_unpack_i (
    	.packet(umi_rx_packet),
        .data(rx_data),
        .srcaddr(rx_srcaddr),
        .dstaddr(rx_dstaddr),
		
        // unused outputs
        .write(),
        .command(),
        .size(),
        .options()
    );

    assign rx_opcode = umi_rx_packet[7:0];
    assign rx_cmd_read = (rx_opcode == READ_REQUEST) ? 1'b1 : 1'b0;
    assign rx_cmd_write = (rx_opcode == WRITE_POSTED) ? 1'b1 : 1'b0;    

    // form outgoing packet (which can only be a read response)

    reg [63:0] tx_dstaddr;
    reg [255:0] tx_data;

    /* verilator lint_off WIDTH */
    localparam [3:0] UMI_SIZE = $clog2(DATA_WIDTH/8);
    /* verilator lint_on WIDTH */

	umi_pack umi_pack_i (
		.write(WRITE_RESPONSE[0]),
        .command(WRITE_RESPONSE[7:1]),
		.size(UMI_SIZE),
		.options(20'd0),
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
