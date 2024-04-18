// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module axi_reader #(
    parameter ID_WIDTH = 16
) (
    input wire clk,

    input wire rvalid,
    input wire [63:0] raddr,
    output wire [511:0] rdata,
    output wire rready,

    output wire [ID_WIDTH-1:0] m_axi_arid,
    output wire [63:0] m_axi_araddr,
    output wire [7:0] m_axi_arlen,
    output wire [2:0] m_axi_arsize,
    output wire m_axi_arvalid,
    input wire m_axi_arready,

    input wire [ID_WIDTH-1:0] m_axi_rid,
    input wire [511:0] m_axi_rdata,
    input wire [1:0] m_axi_rresp,
    input wire m_axi_rlast,
    input wire m_axi_rvalid,
    output wire m_axi_rready
);

    localparam [1:0] STATE_IDLE = 2'd0;
    localparam [1:0] STATE_READ = 2'd1;
    localparam [1:0] STATE_WAIT_RESP = 2'd2;

    reg [1:0] state = STATE_IDLE;
    reg [1:0] state_next;

    always @(*) begin
        state_next = state;
        case (state)
            STATE_IDLE: begin
                if (rvalid) begin
                    state_next = STATE_READ;
                end
            end

            STATE_READ: begin
                if (m_axi_arready) begin
                    state_next = STATE_WAIT_RESP;
                end
            end

            STATE_WAIT_RESP: begin
                if (m_axi_rvalid) begin
                    state_next = STATE_IDLE;
                end
            end

            // Shouldn't reach here
            default: state_next = 2'bXX;
        endcase
    end

    always @(posedge clk) begin
        state <= state_next;
    end

    // Pulse rready after we get response
    assign rready = (state == STATE_WAIT_RESP) && (state_next == STATE_IDLE);
    assign rdata = m_axi_rdata;

    assign m_axi_arid = {ID_WIDTH{1'b0}};
    assign m_axi_araddr = raddr;
    assign m_axi_arlen = 8'b0;
    assign m_axi_arsize = 3'd6;
    assign m_axi_arvalid = (state == STATE_READ);

    assign m_axi_rready = (state == STATE_WAIT_RESP);

endmodule

`default_nettype wire
