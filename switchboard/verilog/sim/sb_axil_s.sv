// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_axil_s #(
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
    input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input  wire [2:0]            s_axil_awprot,
    input  wire                  s_axil_awvalid,
    output wire                  s_axil_awready,
    input  wire [DATA_WIDTH-1:0] s_axil_wdata,
    input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
    input  wire                  s_axil_wvalid,
    output wire                  s_axil_wready,
    output wire [1:0]            s_axil_bresp,
    output wire                  s_axil_bvalid,
    input  wire                  s_axil_bready,
    input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
    input  wire [2:0]            s_axil_arprot,
    input  wire                  s_axil_arvalid,
    output wire                  s_axil_arready,
    output wire [DATA_WIDTH-1:0] s_axil_rdata,
    output wire [1:0]            s_axil_rresp,
    output wire                  s_axil_rvalid,
    input  wire                  s_axil_rready
);
    // AW channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(ADDR_WIDTH + 3)
    ) aw_channel (
        .clk(clk),
        .data({s_axil_awprot, s_axil_awaddr}),
        .dest(),
        .last(),
        .valid(s_axil_awvalid),
        .ready(s_axil_awready)
    );

    // W channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(DATA_WIDTH + STRB_WIDTH)
    ) w_channel (
        .clk(clk),
        .data({s_axil_wstrb, s_axil_wdata}),
        .dest(),
        .last(),
        .valid(s_axil_wvalid),
        .ready(s_axil_wready)
    );

    // B channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(2)
    ) b_channel (
        .clk(clk),
        .data(s_axil_bresp),
        .dest(),
        .last(),
        .valid(s_axil_bvalid),
        .ready(s_axil_bready)
    );

    // AR channel

    sb_to_queue_sim #(
        .READY_MODE_DEFAULT(READY_MODE_DEFAULT),
        .DW(ADDR_WIDTH + 3)
    ) ar_channel (
        .clk(clk),
        .data({s_axil_arprot, s_axil_araddr}),
        .dest(),
        .last(),
        .valid(s_axil_arvalid),
        .ready(s_axil_arready)
    );

    // R channel

    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(DATA_WIDTH + 2)
    ) r_channel (
        .clk(clk),
        .data({s_axil_rresp, s_axil_rdata}),
        .dest(),
        .last(),
        .valid(s_axil_rvalid),
        .ready(s_axil_rready)
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
        b_channel.set_valid_mode(value);
        r_channel.set_valid_mode(value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_START_FUNC set_ready_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        aw_channel.set_ready_mode(value);
        w_channel.set_ready_mode(value);
        ar_channel.set_ready_mode(value);
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
