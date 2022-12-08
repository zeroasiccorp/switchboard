`default_nettype none

module axi_writer (
    input wire clk,

    input wire wvalid,
    input wire [63:0] waddr,
    input wire [63:0] wstrb,
    input wire [511:0] wdata,
    output wire wready,

    output wire [15:0] m_axi_awid,
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

    input wire [15:0] m_axi_bid,
    input wire [1:0] m_axi_bresp,
    input wire m_axi_bvalid,
    output wire m_axi_bready
);

    localparam [1:0] STATE_IDLE = 2'd0;
    localparam [1:0] STATE_WR_ADDR = 2'd1;
    localparam [1:0] STATE_WR_DATA = 2'd2;
    localparam [1:0] STATE_WAIT_RESP = 2'd3;

    reg [1:0] state = STATE_IDLE;
    reg [1:0] state_next;

    always @(*) begin
        state_next = state;
        case (state)
            STATE_IDLE: begin
                if (wvalid) begin
                    state_next = STATE_WR_ADDR;
                end
            end

            STATE_WR_ADDR: begin
                if (m_axi_awready) begin
                    state_next = STATE_WR_DATA;
                end
            end

            STATE_WR_DATA: begin
                if (m_axi_wready) begin
                    state_next = STATE_WAIT_RESP;
                end
            end

            STATE_WAIT_RESP: begin
                if (m_axi_bvalid) begin
                    state_next = STATE_IDLE;
                end
            end
        endcase
    end

    always @(posedge clk) begin
        state <= state_next;
    end

    // Pulse wready after we get response
    assign wready = (state == STATE_WAIT_RESP) && (state_next == STATE_IDLE);

    assign m_axi_awid = 16'b0;
    assign m_axi_awaddr = waddr;
    assign m_axi_awlen = 8'b0;
    assign m_axi_awsize = 3'd6;
    assign m_axi_awvalid = (state == STATE_WR_ADDR);

    assign m_axi_wdata = wdata;
    assign m_axi_wstrb = wstrb;
    assign m_axi_wlast = 1'b1;
    assign m_axi_wvalid = (state == STATE_WR_DATA);

    assign m_axi_bready = (state == STATE_WAIT_RESP);

endmodule

`default_nettype wire
