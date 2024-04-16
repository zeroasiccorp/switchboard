// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_rx_fpga #(
    parameter ID_WIDTH = 16,
    // must be <= 448 (512-64)
    parameter DW = 416
) (
    input wire clk,
    input wire en,
    input wire reset,

    output reg [DW-1:0] data={DW{1'b0}},
    output reg [31:0] dest=32'b0,
    output reg last=1'b0,
    input wire ready,
    output reg valid=1'b0,

    input wire [63:0] cfg_base_addr,
    input wire [31:0] cfg_capacity,

    output wire status_idle,

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
    output wire m_axi_bready,

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

    `include "spsc_queue.vh"

    /*
     * Main state machine
     */

    localparam [2:0] STATE_IDLE = 3'd0;
    localparam [2:0] STATE_RD_HEAD = 3'd1;
    localparam [2:0] STATE_RD_PACKET = 3'd2;
    localparam [2:0] STATE_WR_TAIL = 3'd3;
    localparam [2:0] STATE_FAULT = 3'd4;

    wire wvalid;
    reg [63:0] waddr;
    reg [63:0] wstrb;
    reg [511:0] wdata;
    wire wready;

    wire rvalid;
    reg [63:0] raddr;
    wire rready;
    wire [511:0] rdata;

    wire empty;
    wire fault;

    reg [2:0] state = STATE_IDLE;
    reg [2:0] state_next;

    always @(*) begin
        state_next = state;
        case (state)
            STATE_IDLE: begin
                if (!valid && en) begin
                    if (!empty) begin
                        state_next = STATE_RD_PACKET;
                    end else begin
                        state_next = STATE_RD_HEAD;
                    end
                end
            end

            STATE_RD_HEAD: begin
                if (rready && !en) begin
                    state_next = STATE_IDLE;
                end else if (!empty) begin
                    state_next = STATE_RD_PACKET;
                end
            end

            STATE_RD_PACKET: begin
                // This state doesn't force a transition to IDLE on !en, since
                // we always need to write the tail after reading the packet.
                if (rready) begin
                    state_next = STATE_WR_TAIL;
                end
            end

            STATE_WR_TAIL: begin
                if (wready) begin
                    state_next = STATE_IDLE;
                end
            end

            STATE_FAULT: begin
                state_next = STATE_FAULT;
            end

            // Shouldn't reach here
            default: state_next = 3'bXXX;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= STATE_IDLE;
        end else if (fault) begin
            state <= STATE_FAULT;
        end else begin
            state <= state_next;
        end
    end

    /*
     * Queue state logic
     */

    reg [31:0] head = 32'd0;
    reg [31:0] tail = 32'd0;
    wire [31:0] head_next;
    wire [31:0] tail_next;
    wire [31:0] tail_incr;

    assign head_next = (state == STATE_RD_HEAD && rready) ? rdata[31:0] : head;

    assign tail_incr = (tail + 32'd1 == cfg_capacity) ? 32'd0 : (tail + 32'd1);
    assign tail_next = (state == STATE_RD_PACKET && rready) ? tail_incr : tail;

    always @(posedge clk) begin
        if (reset) begin
            head <= 32'd0;
            tail <= 32'd0;
        end else begin
            head <= head_next;
            tail <= tail_next;
        end
    end

    // Use *_next signals here to speed up state machine transitions.
    assign empty = (head_next == tail_next);

    // Addresses within queue
    wire [63:0] head_addr;
    wire [63:0] tail_addr;
    assign head_addr = cfg_base_addr + HEAD_OFFSET;
    assign tail_addr = cfg_base_addr + TAIL_OFFSET;

    /*
     * Checker for out-of-bounds writes
     */

    wire wvalid_checked;
    wire [63:0] fault_addr;
    memory_fault write_checker(
        .clk(clk),
        .reset(reset),

        .access_valid_in(wvalid),
        .access_addr(waddr),
        .access_valid_out(wvalid_checked),

        .base_legal_addr(cfg_base_addr),
        .legal_length(cfg_capacity * PACKET_SIZE + PACKET_OFFSET),

        .fault(fault),
        .fault_addr(fault_addr)
    );

    /*
     * Simple W/R interface to AXI bus
     */

    axi_writer #(
        .ID_WIDTH(ID_WIDTH)
    ) writer (
        .wvalid(wvalid_checked),
        .*
    );

    axi_reader #(
        .ID_WIDTH(ID_WIDTH)
    ) reader (
        .*
    );

    assign wvalid = (state == STATE_WR_TAIL);
    always @(*) begin
        waddr = 64'd0;
        wstrb = 64'd0;
        wdata = 512'd0;
        if (state == STATE_WR_TAIL) begin
            waddr = tail_addr;
            wstrb = 64'hff;
            wdata = {480'd0, tail};
        end
    end
    assign rvalid = ((state == STATE_RD_HEAD) || (state == STATE_RD_PACKET));
    always @(*) begin
        raddr = 64'd0;
        if (state == STATE_RD_HEAD) begin
            raddr = head_addr;
        end else if (state == STATE_RD_PACKET) begin
            raddr = cfg_base_addr + PACKET_OFFSET + (tail * PACKET_SIZE);
        end
    end

    /*
     * SB handshaking
     */

    // This logic relies on maintaining invariant that valid != 1 when state ==
    // STATE_RD_PACKET
    always @(posedge clk) begin
        if (reset) begin
            valid <= 1'b0;
            dest <= 32'd0;
            last <= 1'b0;
            data <= 'd0;
        end else if (state == STATE_RD_PACKET && rready) begin
            valid <= 1'b1;
            dest <= rdata[31:0];
            last <= rdata[32];
            data <= rdata[DW+64-1:64];
        end else if (valid && ready) begin
            valid <= 1'b0;
        end
    end

    assign status_idle = state == STATE_IDLE;

`ifdef DEBUG
   ila_0 ILA_RD (
                   .clk    (clk),
                   .probe0 (m_axi_arvalid),
                   .probe1 (m_axi_araddr),
                   .probe2 (m_axi_arready),
                   .probe3 (m_axi_rvalid),
                   .probe4 (m_axi_rdata[63:0]),
                   .probe5 (m_axi_rready)
                   );

   ila_0 ILA_WR (
                   .clk    (clk),
                   .probe0 (m_axi_awvalid),
                   .probe1 (m_axi_awaddr),
                   .probe2 (m_axi_awready),
                   .probe3 (m_axi_wvalid),
                   .probe4 (m_axi_wdata[63:0]),
                   .probe5 (m_axi_wready)
                   );

   ila_0 ILA_STATE (
                   .clk    (clk),
                   .probe0 (en),
                   .probe1 ({head, tail}),
                   .probe2 (valid),
                   .probe3 (ready),
                   .probe4 ({state, tail_incr}),
                   .probe5 (empty)
                   );

   ila_0 ILA_FAULT (
                   .clk    (clk),
                   .probe0 (fault),
                   .probe1 (fault_addr),
                   .probe2 (),
                   .probe3 (),
                   .probe4 (),
                   .probe5 ()
                   );
`endif

endmodule

`default_nettype wire
