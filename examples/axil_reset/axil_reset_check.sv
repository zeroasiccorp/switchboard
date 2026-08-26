// AXI-Lite subordinate that models the class of DUT described in
// https://github.com/zeroasiccorp/switchboard/issues/275: a "simple axi lite
// register interface" whose handshake logic ignores reset, so "ready" is high
// by default -- including while the design is still in reset.
//
// A transactor that drives transactions without regard to reset will have them
// accepted before the design is ready.  In a real DUT those transactions are
// silently dropped and the simulation hangs waiting for a response that never
// comes.  To keep the failure observable rather than fatal, this model still
// responds to every transaction, and counts the ones that were accepted while
// reset was asserted.  The count is readable over the same AXI-Lite port, so
// the testbench can assert that it is zero.

// Copyright (c) 2026 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module axil_reset_check #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 8,
    parameter STRB_WIDTH = (DATA_WIDTH/8)
) (
    input  wire                  clk,
    input  wire                  rst,

    // AXI-Lite subordinate interface
    input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input  wire [2:0]            s_axil_awprot,
    input  wire                  s_axil_awvalid,
    output wire                  s_axil_awready,
    input  wire [DATA_WIDTH-1:0] s_axil_wdata,
    input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
    input  wire                  s_axil_wvalid,
    output wire                  s_axil_wready,
    output wire [1:0]            s_axil_bresp,
    output reg                   s_axil_bvalid = 1'b0,
    input  wire                  s_axil_bready,
    input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
    input  wire [2:0]            s_axil_arprot,
    input  wire                  s_axil_arvalid,
    output wire                  s_axil_arready,
    output reg  [DATA_WIDTH-1:0] s_axil_rdata = 'b0,
    output wire [1:0]            s_axil_rresp,
    output reg                   s_axil_rvalid = 1'b0,
    input  wire                  s_axil_rready
);
    // unused inputs
    /* verilator lint_off UNUSEDSIGNAL */
    wire [ADDR_WIDTH-1:0] unused_awaddr = s_axil_awaddr;
    wire [2:0]            unused_awprot = s_axil_awprot;
    wire [DATA_WIDTH-1:0] unused_wdata = s_axil_wdata;
    wire [STRB_WIDTH-1:0] unused_wstrb = s_axil_wstrb;
    wire [ADDR_WIDTH-1:0] unused_araddr = s_axil_araddr;
    wire [2:0]            unused_arprot = s_axil_arprot;
    /* verilator lint_on UNUSEDSIGNAL */

    assign s_axil_bresp = 2'b00;
    assign s_axil_rresp = 2'b00;

    // the write halves are tracked independently, and "ready" is simply the
    // absence of anything outstanding.  nothing here is gated on rst, which is
    // the whole point of the model: at time zero all three ready signals are
    // high, so a transactor that ignores reset gets its transactions accepted.

    reg aw_pending = 1'b0;
    reg w_pending = 1'b0;

    assign s_axil_awready = !aw_pending;
    assign s_axil_wready = !w_pending;
    assign s_axil_arready = !s_axil_rvalid;

    wire aw_accepted = s_axil_awvalid && s_axil_awready;
    wire w_accepted = s_axil_wvalid && s_axil_wready;
    wire ar_accepted = s_axil_arvalid && s_axil_arready;

    // count transactions accepted while reset was asserted.  deliberately not
    // cleared by rst -- it is a record of what happened during reset.
    localparam CNT_WIDTH = 8;

    reg [CNT_WIDTH-1:0] rst_xacts = 'b0;

    always @(posedge clk) begin
        if (rst && (aw_accepted || ar_accepted)) begin
            if (rst_xacts != {CNT_WIDTH{1'b1}}) begin
                rst_xacts <= rst_xacts + 1'b1;
            end
        end
    end

    always @(posedge clk) begin
        // write address / data
        if (aw_accepted) begin
            aw_pending <= 1'b1;
        end

        if (w_accepted) begin
            w_pending <= 1'b1;
        end

        // issue the write response once both halves have arrived
        if (aw_pending && w_pending && !s_axil_bvalid) begin
            s_axil_bvalid <= 1'b1;
            aw_pending <= 1'b0;
            w_pending <= 1'b0;
        end else if (s_axil_bvalid && s_axil_bready) begin
            s_axil_bvalid <= 1'b0;
        end

        // every read returns the number of transactions accepted during reset
        if (ar_accepted) begin
            s_axil_rvalid <= 1'b1;
            s_axil_rdata <= {{(DATA_WIDTH-CNT_WIDTH){1'b0}}, rst_xacts};
        end else if (s_axil_rvalid && s_axil_rready) begin
            s_axil_rvalid <= 1'b0;
        end
    end

endmodule

`default_nettype wire
