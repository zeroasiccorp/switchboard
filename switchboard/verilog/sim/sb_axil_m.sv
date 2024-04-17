// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_axil_m #(
    // AXI settings
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 16,
    parameter STRB_WIDTH = (DATA_WIDTH/8),

    // Switchboard settings
    parameter integer VALID_MODE_DEFAULT=1,
    parameter integer READY_MODE_DEFAULT=1,
    parameter FILE=""
) (
    input wire clk,

    // AXI lite master interface
    // adapted from https://github.com/alexforencich/verilog-axi
    output wire [ADDR_WIDTH-1:0] m_axil_awaddr,
    output wire [2:0]            m_axil_awprot,
    output wire                  m_axil_awvalid,
    input  wire                  m_axil_awready,
    output wire [DATA_WIDTH-1:0] m_axil_wdata,
    output wire [STRB_WIDTH-1:0] m_axil_wstrb,
    output wire                  m_axil_wvalid,
    input  wire                  m_axil_wready,
    input  wire [1:0]            m_axil_bresp,
    input  wire                  m_axil_bvalid,
    output wire                  m_axil_bready,
    output wire [ADDR_WIDTH-1:0] m_axil_araddr,
    output wire [2:0]            m_axil_arprot,
    output wire                  m_axil_arvalid,
    input  wire                  m_axil_arready,
    input  wire [DATA_WIDTH-1:0] m_axil_rdata,
    input  wire [1:0]            m_axil_rresp,
    input  wire                  m_axil_rvalid,
    output wire                  m_axil_rready
);
    // AW channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(ADDR_WIDTH + 3)
    ) aw_channel (
        .clk(clk),
        .data({m_axil_awprot, m_axil_awaddr}),
        .dest(),
        .last(),
        .valid(m_axil_awvalid),
        .ready(m_axil_awready)
    );

    // W channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(DATA_WIDTH + STRB_WIDTH)
    ) w_channel (
        .clk(clk),
        .data({m_axil_wstrb, m_axil_wdata}),
        .dest(),
        .last(),
        .valid(m_axil_wvalid),
        .ready(m_axil_wready)
    );

    // B channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(2)
    ) b_channel (
        .clk(clk),
        .data(m_axil_bresp),
        .dest(),
        .last(),
        .valid(m_axil_bvalid),
        .ready(m_axil_bready)
    );

    // AR channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(ADDR_WIDTH + 3)
    ) ar_channel (
        .clk(clk),
        .data({m_axil_arprot, m_axil_araddr}),
        .dest(),
        .last(),
        .valid(m_axil_arvalid),
        .ready(m_axil_arready)
    );

    // R channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(DATA_WIDTH + 2)
    ) r_channel (
        .clk(clk),
        .data({m_axil_rresp, m_axil_rdata}),
        .dest(),
        .last(),
        .valid(m_axil_rvalid),
        .ready(m_axil_rready)
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
