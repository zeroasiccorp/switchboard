module umiram #(
    parameter integer ADDR_WIDTH=8,
    parameter integer DATA_WIDTH=32,
    parameter integer ATOMIC_WIDTH=64
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

    wire [63:0] rx_dstaddr;
    wire [63:0] rx_srcaddr;
    wire [255:0] rx_data;
    wire [3:0] rx_size;

    umi_unpack umi_unpack_i (
        .packet(umi_rx_packet),
        .data(rx_data),
        .srcaddr(rx_srcaddr),
        .dstaddr(rx_dstaddr),
        .size(rx_size),

        // unused outputs
        .write(),
        .command(),
        .options()
    );

    wire [7:0] rx_opcode;
    assign rx_opcode = umi_rx_packet[7:0];

    wire rx_cmd_read;
    assign rx_cmd_read = (rx_opcode == READ_REQUEST) ? 1'b1 : 1'b0;

    wire rx_cmd_write;
    assign rx_cmd_write = (rx_opcode == WRITE_POSTED) ? 1'b1 : 1'b0;

    wire rx_cmd_atomic;
    assign rx_cmd_atomic = (rx_opcode[3:0] == 4'h4) ? 1'b1 : 1'b0;

    // form outgoing packet (which can only be a read response)

    wire tx_write;
    wire [6:0] tx_command;

    reg [63:0] tx_dstaddr;
    reg [255:0] tx_data;
    reg [3:0] tx_size;

    assign tx_write = WRITE_RESPONSE[0];
    assign tx_command = WRITE_RESPONSE[7:1];

    umi_pack umi_pack_i (
        .write(tx_write),
        .command(tx_command),
        .size(tx_size),
        .options(20'd0),
        .burst(1'b0),
        .dstaddr(tx_dstaddr),
        .srcaddr(64'd0),
        .data(tx_data),
        .packet(umi_tx_packet)
    );

    // main logic

    reg [((2**ADDR_WIDTH)*8-1):0] mem;

    wire [15:0] nbytes;
    assign nbytes = 16'd1<<{12'd0, rx_size};

    integer i;

    function [ATOMIC_WIDTH-1:0] atomic_op(input [ATOMIC_WIDTH-1:0] a,
        input [ATOMIC_WIDTH-1:0] b, input [3:0] size, input [7:0] opcode);

        integer nbits;
        integer nshift;
        reg signed [ATOMIC_WIDTH-1:0] aval;
        reg [ATOMIC_WIDTH-1:0] avalu;
        reg signed [ATOMIC_WIDTH-1:0] bval;
        reg [ATOMIC_WIDTH-1:0] bvalu;

        nbits = (32'd1 << {28'd0, size}) << 32'd3;
        if (nbits > ATOMIC_WIDTH) begin
            nbits = ATOMIC_WIDTH;
        end

        nshift = ATOMIC_WIDTH - nbits;

        avalu = (a << nshift) >> nshift;
        bvalu = (b << nshift) >> nshift;

        aval = (a <<< nshift) >>> nshift;
        bval = (b <<< nshift) >>> nshift;

        if (opcode == ATOMIC_SWAP) begin
            atomic_op = bval;
        end else if (opcode == ATOMIC_ADD) begin
            atomic_op = aval + bval;
        end else if (opcode == ATOMIC_AND) begin
            atomic_op = aval & bval;
        end else if (opcode == ATOMIC_OR) begin
            atomic_op = aval | bval;
        end else if (opcode == ATOMIC_XOR) begin
            atomic_op = aval ^ bval;
        end else if (opcode == ATOMIC_MIN) begin
            atomic_op = (aval <= bval) ? aval : bval;
        end else if (opcode == ATOMIC_MAX) begin
            atomic_op = (aval >= bval) ? aval : bval;
        end else if (opcode == ATOMIC_MINU) begin
            atomic_op = (avalu <= bvalu) ? avalu : bvalu;
        end else if (opcode == ATOMIC_MAXU) begin
            atomic_op = (avalu >= bvalu) ? avalu : bvalu;
        end else begin
            atomic_op = '0;
        end
    endfunction

    reg [ATOMIC_WIDTH-1:0] a_atomic;
    reg [ATOMIC_WIDTH-1:0] b_atomic;
    reg [ATOMIC_WIDTH-1:0] y_atomic;

    always @(posedge clk) begin
        // handle receiver
        if (umi_rx_valid && umi_rx_ready) begin
            umi_rx_ready <= 1'b0;
        end else if (umi_rx_valid) begin
            if (rx_cmd_write) begin
                for (i=0; i<nbytes; i=i+1) begin
                    mem[(i+rx_dstaddr)*8 +: 8] <= rx_data[i*8 +: 8];
                end
                umi_rx_ready <= 1'b1;
            end else if ((rx_cmd_read || rx_cmd_atomic) && !umi_tx_valid) begin
                for (i=0; i<nbytes; i=i+1) begin
                    tx_data[i*8 +: 8] <= mem[(i+rx_dstaddr)*8 +: 8];
                    if (rx_cmd_atomic) begin
                        // blocking assignment
                        a_atomic[i*8 +: 8] = mem[(i+rx_dstaddr)*8 +: 8];
                    end
                end
                if (rx_cmd_atomic) begin
                    for (i=0; i<nbytes; i=i+1) begin
                        // blocking assignment
                        b_atomic[i*8 +: 8] = rx_data[i*8 +: 8];
                    end
                    // blocking assignment
                    y_atomic = atomic_op(a_atomic, b_atomic, rx_size, rx_opcode);
                    for (i=0; i<nbytes; i=i+1) begin
                        mem[(i+rx_dstaddr)*8 +: 8] <= y_atomic[i*8 +: 8];
                    end
                end                
                tx_dstaddr <= rx_srcaddr;
                tx_size <= rx_size;
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
