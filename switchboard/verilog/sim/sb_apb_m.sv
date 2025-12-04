// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module sb_apb_m #(
    // AXI settings
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 16,
    parameter STRB_WIDTH = (DATA_WIDTH/8),

    // Switchboard settings
    parameter integer VALID_MODE_DEFAULT=1,
    parameter FILE=""
) (
    input wire clk,
    input wire reset,

    // APB master interface
    output wire                     m_apb_psel,
    output wire                     m_apb_penable,
    output wire                     m_apb_pwrite,
    output wire [2:0]               m_apb_pprot,
    output wire [ADDR_WIDTH-1:0]    m_apb_paddr,
    output wire [STRB_WIDTH-1:0]    m_apb_pstrb,
    output wire [DATA_WIDTH-1:0]    m_apb_pwdata,
    input  wire [DATA_WIDTH-1:0]    m_apb_prdata,
    input  wire                     m_apb_pready,
    input  wire                     m_apb_pslverr
);

    // APB FSM state register type
    typedef enum logic [1:0] {
        APB_IDLE,
        APB_SETUP,
        APB_ACCESS
    } apb_state_t;

    // Wires
    wire apb_trans_avail;
    wire apb_fire;

    // APB FSM state register
    apb_state_t apb_state;

    // APB request channel
    queue_to_sb_sim #(
        .VALID_MODE_DEFAULT(VALID_MODE_DEFAULT),
        .DW(1 + 3 + STRB_WIDTH + ADDR_WIDTH + DATA_WIDTH)
    ) apb_req_channel (
        .clk(clk),
        .reset(reset),
        .data({m_apb_pwrite, m_apb_pprot, m_apb_pstrb, m_apb_paddr, m_apb_pwdata}),
        .dest(),
        .last(),
        .valid(apb_trans_avail),
        .ready(apb_fire)
    );

    // APB response channel
    sb_to_queue_sim #(
        // Queue should always be ready to receive responses
        .READY_MODE_DEFAULT(1),
        .DW(DATA_WIDTH + 1)
    ) apb_resp_channel (
        .clk(clk),
        .reset(reset),
        .data({m_apb_pslverr, m_apb_prdata}),
        .dest(),
        .last(),
        .valid(apb_fire),
        .ready()
    );

    // APB master state machine
    always_ff @(posedge clk or posedge reset)
        if (reset)
            apb_state <= APB_IDLE;
        else
            case (apb_state)
                APB_IDLE:
                    if (apb_trans_avail) apb_state <= APB_SETUP;
                APB_SETUP:
                    apb_state <= APB_ACCESS;
                APB_ACCESS:
                    if (m_apb_pready) apb_state <= APB_IDLE;
                default:
                    apb_state <= APB_IDLE;
            endcase

    assign m_apb_psel = (apb_state == APB_SETUP || apb_state == APB_ACCESS);
    assign m_apb_penable = (apb_state == APB_ACCESS);
    assign apb_fire = m_apb_psel & m_apb_penable & m_apb_pready;

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
        $sformat(s, "%0s_apb_req.q", uri);
        apb_req_channel.init(s);

        $sformat(s, "%0s_apb_resp.q", uri);
        apb_resp_channel.init(s);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_START_FUNC set_valid_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        apb_req_channel.set_valid_mode(value);
        /* verilator lint_on IGNOREDRETURN */
    `SB_END_FUNC

    `SB_START_FUNC set_ready_mode(input integer value);
        /* verilator lint_off IGNOREDRETURN */
        apb_resp_channel.set_ready_mode(value);
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
