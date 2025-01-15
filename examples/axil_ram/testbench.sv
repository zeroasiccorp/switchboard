/*******************************************************************************
 * Copyright 2025 Zero ASIC Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * ----
 *
 * Documentation:
 * - Testbench for AXIL Ram using switchboard
 *
 ******************************************************************************/

`default_nettype none

`include "switchboard.vh"

module testbench (
`ifdef VERILATOR
    input clk
`endif
);

    localparam ADDR_WIDTH   = 8;
    localparam DATA_WIDTH   = 256;
    localparam STRB_WIDTH   = (DATA_WIDTH/8);

    localparam PERIOD_CLK   = 10;
    localparam RST_CYCLES   = 16;

`ifndef VERILATOR
    // Generate clock for non verilator sim tools
    reg clk;

    initial
        clk  = 1'b0;
    always #(PERIOD_CLK/2) clk = ~clk;
`endif

    // Reset control
    reg [RST_CYCLES:0]      nreset_vec;
    wire                    nreset;
    wire                    initdone;

    assign nreset = nreset_vec[RST_CYCLES-1];
    assign initdone = nreset_vec[RST_CYCLES];

    initial
        nreset_vec = 'b1;
    always @(negedge clk) nreset_vec <= {nreset_vec[RST_CYCLES-1:0], 1'b1};

    wire [ADDR_WIDTH-1:0]  s_axil_awaddr;
    wire [2:0]             s_axil_awprot;
    wire                   s_axil_awvalid;
    wire                   s_axil_awready;

    wire [DATA_WIDTH-1:0]  s_axil_wdata;
    wire [STRB_WIDTH-1:0]  s_axil_wstrb;
    wire                   s_axil_wvalid;
    wire                   s_axil_wready;

    wire [1:0]             s_axil_bresp;
    wire                   s_axil_bvalid;
    wire                   s_axil_bready;

    wire [ADDR_WIDTH-1:0]  s_axil_araddr;
    wire [2:0]             s_axil_arprot;
    wire                   s_axil_arvalid;
    wire                   s_axil_arready;

    wire [DATA_WIDTH-1:0]  s_axil_rdata;
    wire [1:0]             s_axil_rresp;
    wire                   s_axil_rvalid;
    wire                   s_axil_rready;

    axil_ram #(
        .DATA_WIDTH     (DATA_WIDTH),
        .ADDR_WIDTH     (ADDR_WIDTH))
    dut (
        .clk                (clk),
        .rst                (~nreset),

        .s_axil_awaddr      (s_axil_awaddr),
        .s_axil_awprot      (s_axil_awprot),
        .s_axil_awvalid     (s_axil_awvalid),
        .s_axil_awready     (s_axil_awready),

        .s_axil_wdata       (s_axil_wdata),
        .s_axil_wstrb       (s_axil_wstrb),
        .s_axil_wvalid      (s_axil_wvalid),
        .s_axil_wready      (s_axil_wready),

        .s_axil_bresp       (s_axil_bresp),
        .s_axil_bvalid      (s_axil_bvalid),
        .s_axil_bready      (s_axil_bready),

        .s_axil_araddr      (s_axil_araddr),
        .s_axil_arprot      (s_axil_arprot),
        .s_axil_arvalid     (s_axil_arvalid),
        .s_axil_arready     (s_axil_arready),

        .s_axil_rdata       (s_axil_rdata),
        .s_axil_rresp       (s_axil_rresp),
        .s_axil_rvalid      (s_axil_rvalid),
        .s_axil_rready      (s_axil_rready));

    sb_axil_m #(
        .DATA_WIDTH (DATA_WIDTH),
        .ADDR_WIDTH (ADDR_WIDTH))
    sb_axil_m_i (
        .clk            (clk),

        .m_axil_awaddr  (s_axil_awaddr),
        .m_axil_awprot  (s_axil_awprot),
        .m_axil_awvalid (s_axil_awvalid),
        .m_axil_awready (s_axil_awready),

        .m_axil_wdata   (s_axil_wdata),
        .m_axil_wstrb   (s_axil_wstrb),
        .m_axil_wvalid  (s_axil_wvalid),
        .m_axil_wready  (s_axil_wready),

        .m_axil_bresp   (s_axil_bresp),
        .m_axil_bvalid  (s_axil_bvalid),
        .m_axil_bready  (s_axil_bready),

        .m_axil_araddr  (s_axil_araddr),
        .m_axil_arprot  (s_axil_arprot),
        .m_axil_arvalid (s_axil_arvalid),
        .m_axil_arready (s_axil_arready),

        .m_axil_rdata   (s_axil_rdata),
        .m_axil_rresp   (s_axil_rresp),
        .m_axil_rvalid  (s_axil_rvalid),
        .m_axil_rready  (s_axil_rready));

    // Initialize queues/modes
    integer valid_mode, ready_mode;

    initial begin
        if (!$value$plusargs("valid_mode=%d", valid_mode)) begin
           valid_mode = 2;  // default if not provided as a plusarg
        end

        if (!$value$plusargs("ready_mode=%d", ready_mode)) begin
           ready_mode = 2;  // default if not provided as a plusarg
        end

        sb_axil_m_i.init("sb_axil_m");
        sb_axil_m_i.set_valid_mode(valid_mode);
        sb_axil_m_i.set_ready_mode(ready_mode);
    end

    // control block
    `SB_SETUP_PROBES

    // auto-stop
    auto_stop_sim auto_stop_sim_i (.clk(clk));

endmodule

`default_nettype wire
