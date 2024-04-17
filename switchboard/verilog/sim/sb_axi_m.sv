// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_axi_m #(
    // AXI settings
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 16,
    parameter STRB_WIDTH = (DATA_WIDTH/8),
    parameter ID_WIDTH = 8,

    // Switchboard settings
    parameter integer VALID_MODE_DEFAULT=1,
    parameter integer READY_MODE_DEFAULT=1,
    parameter FILE=""
) (
    input wire clk,

    // AXI master interface
    // adapted from https://github.com/alexforencich/verilog-axi
    output wire [ID_WIDTH-1:0]    m_axi_awid,
    output wire [ADDR_WIDTH-1:0]  m_axi_awaddr,
    output wire [7:0]             m_axi_awlen,
    output wire [2:0]             m_axi_awsize,
    output wire [1:0]             m_axi_awburst,
    output wire                   m_axi_awlock,
    output wire [3:0]             m_axi_awcache,
    output wire [2:0]             m_axi_awprot,
    output wire                   m_axi_awvalid,
    input  wire                   m_axi_awready,
    output wire [DATA_WIDTH-1:0]  m_axi_wdata,
    output wire [STRB_WIDTH-1:0]  m_axi_wstrb,
    output wire                   m_axi_wlast,
    output wire                   m_axi_wvalid,
    input  wire                   m_axi_wready,
    input  wire [ID_WIDTH-1:0]    m_axi_bid,
    input  wire [1:0]             m_axi_bresp,
    input  wire                   m_axi_bvalid,
    output wire                   m_axi_bready,
    output wire [ID_WIDTH-1:0]    m_axi_arid,
    output wire [ADDR_WIDTH-1:0]  m_axi_araddr,
    output wire [7:0]             m_axi_arlen,
    output wire [2:0]             m_axi_arsize,
    output wire [1:0]             m_axi_arburst,
    output wire                   m_axi_arlock,
    output wire [3:0]             m_axi_arcache,
    output wire [2:0]             m_axi_arprot,
    output wire                   m_axi_arvalid,
    input  wire                   m_axi_arready,
    input  wire [ID_WIDTH-1:0]    m_axi_rid,
    input  wire [DATA_WIDTH-1:0]  m_axi_rdata,
    input  wire [1:0]             m_axi_rresp,
    input  wire                   m_axi_rlast,
    input  wire                   m_axi_rvalid,
    output wire                   m_axi_rready
);
    // AW channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(ADDR_WIDTH + 3 + ID_WIDTH + 8 + 3 + 2 + 1 + 4)
    ) aw_channel (
        .clk(clk),
        .data({m_axi_awcache, m_axi_awlock, m_axi_awburst, m_axi_awsize,
            m_axi_awlen, m_axi_awid, m_axi_awprot, m_axi_awaddr}),
        .dest(),
        .last(),
        .valid(m_axi_awvalid),
        .ready(m_axi_awready)
    );

    // W channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(DATA_WIDTH + STRB_WIDTH + 1)
    ) w_channel (
        .clk(clk),
        .data({m_axi_wlast, m_axi_wstrb, m_axi_wdata}),
        .dest(),
        .last(),
        .valid(m_axi_wvalid),
        .ready(m_axi_wready)
    );

    // B channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(2 + ID_WIDTH)
    ) b_channel (
        .clk(clk),
        .data({m_axi_bid, m_axi_bresp}),
        .dest(),
        .last(),
        .valid(m_axi_bvalid),
        .ready(m_axi_bready)
    );

    // AR channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(ADDR_WIDTH + 3 + ID_WIDTH + 8 + 3 + 2 + 1 + 4)
    ) ar_channel (
        .clk(clk),
        .data({m_axi_arcache, m_axi_arlock, m_axi_arburst, m_axi_arsize,
            m_axi_arlen, m_axi_arid, m_axi_arprot, m_axi_araddr}),
        .dest(),
        .last(),
        .valid(m_axi_arvalid),
        .ready(m_axi_arready)
    );

    // R channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(DATA_WIDTH + 2 + ID_WIDTH + 1)
    ) r_channel (
        .clk(clk),
        .data({m_axi_rlast, m_axi_rid, m_axi_rresp, m_axi_rdata}),
        .dest(),
        .last(),
        .valid(m_axi_rvalid),
        .ready(m_axi_rready)
    );

    // handle differences between simulators

    `ifdef __ICARUS__
        `define SB_START_FUNC task
        `define SB_END_FUNC endtask
    `else
        `define SB_START_FUNC function void
        `define SB_END_FUNC endfunction
    `endif

    `SB_START_FUNC init(input string uri);
        string s;

        /* verilator lint_off IGNOREDRETURN */
        $sformat(s, "%0s-aw.q", uri);
        aw_channel.init(s);

        $sformat(s, "%0s-w.q", uri);
        w_channel.init(s);

        $sformat(s, "%0s-b.q", uri);
        b_channel.init(s);

        $sformat(s, "%0s-ar.q", uri);
        ar_channel.init(s);

        $sformat(s, "%0s-r.q", uri);
        r_channel.init(s);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_START_FUNC set_valid_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        aw_channel.set_valid_mode(value);
        w_channel.set_valid_mode(value);
        ar_channel.set_valid_mode(value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_START_FUNC set_ready_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        b_channel.set_ready_mode(value);
        r_channel.set_ready_mode(value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    // initialize

    initial begin
        if (FILE != "") begin
            /* verilator lint_off IGNOREDRETURN */
            init(FILE);
            /* verilator lint_on IGNOREDRETURN */
        end
    end

    // clean up macros

    `undef SB_START_FUNC
    `undef SB_END_FUNC

endmodule

`default_nettype wire
