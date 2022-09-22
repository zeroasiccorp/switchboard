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

    wire rx_cmd_read;
    wire rx_cmd_write;
    wire [63:0] rx_dstaddr;
    wire [63:0] rx_srcaddr;
    wire [255:0] rx_data;

	umi_unpack umi_unpack_i (
        // input
    	.packet_in(umi_rx_packet),

        // output
        .data(rx_data),
        .srcaddr(rx_srcaddr),
        .dstaddr(rx_dstaddr),
		.cmd_write(rx_cmd_write),
		.cmd_read(rx_cmd_read),

        // all of these outputs are unused...
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

    // form outgoing packet (which can only be a read response)

    reg [63:0] tx_dstaddr;
    reg [255:0] tx_data;

    /* verilator lint_off WIDTH */
    localparam [3:0] UMI_SIZE = $clog2(DATA_WIDTH/8);
    /* verilator lint_on WIDTH */

	umi_pack umi_pack_i (
		.opcode(8'b0000_0001),  // WRITE-NORMAL
		.size(UMI_SIZE),
		.user(20'd0),
		.burst(1'b0),
		.dstaddr(tx_dstaddr),
		.srcaddr(64'd0),
		.data(tx_data),
		.packet_out(umi_tx_packet)
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
