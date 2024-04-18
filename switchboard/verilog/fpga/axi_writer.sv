// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module axi_writer #(
    parameter ID_WIDTH = 16
) (
    input wire clk,

    input wire wvalid,
    input wire [63:0] waddr,
    input wire [63:0] wstrb,
    input wire [511:0] wdata,
    output wire wready,

    output wire [ID_WIDTH-1:0] m_axi_awid,
    output wire [63:0] m_axi_awaddr,
    output wire [7:0] m_axi_awlen,
    output wire [2:0] m_axi_awsize,
    output wire m_axi_awvalid,
    input wire m_axi_awready,

    output wire [511:0] m_axi_wdata,
    output wire [63:0] m_axi_wstrb,
    output wire m_axi_wlast,
    output wire m_axi_wvalid,
    input wire m_axi_wready,

    input wire [ID_WIDTH-1:0] m_axi_bid,
    input wire [1:0] m_axi_bresp,
    input wire m_axi_bvalid,
    output wire m_axi_bready
);

    localparam [1:0] STATE_IDLE = 2'd0;
    localparam [1:0] STATE_WR_ADDR_DATA = 2'd1;
    localparam [1:0] STATE_WAIT_RESP = 2'd2;

    reg [1:0] state = STATE_IDLE;
    reg [1:0] state_next;

    reg awready_seen = 1'b0;
    reg wready_seen = 1'b0;

    always @(*) begin
        state_next = state;
        case (state)
            STATE_IDLE: begin
                if (wvalid) begin
                    state_next = STATE_WR_ADDR_DATA;
                end
            end

            // m_axi_awready and m_axi_wready may wait for both m_axi_awvalid
            // and m_axi_wvalid to assert before asserting, so we raise both
            // valid signals and wait for both ready signals.
            STATE_WR_ADDR_DATA: begin
                if ((m_axi_awready || awready_seen) && (m_axi_wready || wready_seen)) begin
                    state_next = STATE_WAIT_RESP;
                end
            end

            STATE_WAIT_RESP: begin
                if (m_axi_bvalid) begin
                    state_next = STATE_IDLE;
                end
            end

            default: begin
                // would only get here if state contains "X"
                // or "Z" bits.  this might be a bit more
                // conservative than necessary...
                state_next = 2'bxx;
            end
        endcase
    end

    always @(posedge clk) begin
        state <= state_next;
    end

    always @(posedge clk) begin
        if (state == STATE_IDLE) begin
            awready_seen <= 1'b0;
            wready_seen <= 1'b0;
        end else begin
            awready_seen <= m_axi_awready || awready_seen;
            wready_seen <= m_axi_wready || wready_seen;
        end
    end

    // Pulse wready after we get response
    assign wready = (state == STATE_WAIT_RESP) && (state_next == STATE_IDLE);

    assign m_axi_awid = {ID_WIDTH{1'b0}};
    assign m_axi_awaddr = waddr;
    assign m_axi_awlen = 8'b0;
    assign m_axi_awsize = 3'd6;
    assign m_axi_awvalid = (state == STATE_WR_ADDR_DATA) && (!awready_seen);

    assign m_axi_wdata = wdata;
    assign m_axi_wstrb = wstrb;
    assign m_axi_wlast = 1'b1;
    assign m_axi_wvalid = (state == STATE_WR_ADDR_DATA) && (!wready_seen);

    assign m_axi_bready = (state == STATE_WAIT_RESP);

endmodule

`default_nettype wire
