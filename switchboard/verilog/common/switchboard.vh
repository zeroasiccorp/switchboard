// Swithboard utility macros.

// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`ifndef SWITCHBOARD_VH_
`define SWITCHBOARD_VH_

// ref: https://stackoverflow.com/a/15376637
`define STRINGIFY(x) `"x`"

`define UMI_PORT_WIRES_WIDTHS(prefix, dw, cw, aw)       \
        wire prefix``_valid;                            \
        wire [cw - 1 : 0] prefix``_cmd;                 \
        wire [aw - 1 : 0] prefix``_dstaddr;             \
        wire [aw - 1 : 0] prefix``_srcaddr;             \
        wire [dw - 1 : 0] prefix``_data;                \
        wire prefix``_ready

`define SWITCHBOARD_SIM_PORT(prefix, dw)                        \
    `UMI_PORT_WIRES_WIDTHS(prefix``_req, dw, 32, 64);           \
    `UMI_PORT_WIRES_WIDTHS(prefix``_resp, dw, 32, 64);          \
                                                                \
    initial begin                                               \
        /* verilator lint_off IGNOREDRETURN */                  \
        prefix``_rx.init($sformatf("%s_req.q", `"prefix`"));    \
        prefix``_tx.init($sformatf("%s_resp.q", `"prefix`"));   \
        /* verilator lint_on IGNOREDRETURN */                   \
    end                                                         \
                                                                \
    queue_to_umi_sim #(.DW(dw)) prefix``_rx (                   \
        .clk(clk),                                              \
        .data(prefix``_req_data),                               \
        .srcaddr(prefix``_req_srcaddr),                         \
        .dstaddr(prefix``_req_dstaddr),                         \
        .cmd(prefix``_req_cmd),                                 \
        .ready(prefix``_req_ready),                             \
        .valid(prefix``_req_valid)                              \
    );                                                          \
    umi_to_queue_sim #(.DW(dw)) prefix``_tx (                   \
        .clk(clk),                                              \
        .data(prefix``_resp_data),                              \
        .srcaddr(prefix``_resp_srcaddr),                        \
        .dstaddr(prefix``_resp_dstaddr),                        \
        .cmd(prefix``_resp_cmd),                                \
        .ready(prefix``_resp_ready),                            \
        .valid(prefix``_resp_valid)                             \
    )

`define SB_AXIL_WIRES(signal, dw, aw)                           \
    wire [((aw)-1):0]     signal``_awaddr;                      \
    wire [2:0]            signal``_awprot;                      \
    wire                  signal``_awvalid;                     \
    wire                  signal``_awready;                     \
    wire [((dw)-1):0]     signal``_wdata;                       \
    wire [(((dw)/8)-1):0] signal``_wstrb;                       \
    wire                  signal``_wvalid;                      \
    wire                  signal``_wready;                      \
    wire [1:0]            signal``_bresp;                       \
    wire                  signal``_bvalid;                      \
    wire                  signal``_bready;                      \
    wire [((aw)-1):0]     signal``_araddr;                      \
    wire [2:0]            signal``_arprot;                      \
    wire                  signal``_arvalid;                     \
    wire                  signal``_arready;                     \
    wire [((dw))-1:0]     signal``_rdata;                       \
    wire [1:0]            signal``_rresp;                       \
    wire                  signal``_rvalid;                      \
    wire                  signal``_rready;

`define SB_AXIL_CONNECT(a, b)                                   \
        .a``_awaddr(b``_awaddr),                                \
        .a``_awprot(b``_awprot),                                \
        .a``_awvalid(b``_awvalid),                              \
        .a``_awready(b``_awready),                              \
        .a``_wdata(b``_wdata),                                  \
        .a``_wstrb(b``_wstrb),                                  \
        .a``_wvalid(b``_wvalid),                                \
        .a``_wready(b``_wready),                                \
        .a``_bresp(b``_bresp),                                  \
        .a``_bvalid(b``_bvalid),                                \
        .a``_bready(b``_bready),                                \
        .a``_araddr(b``_araddr),                                \
        .a``_arprot(b``_arprot),                                \
        .a``_arvalid(b``_arvalid),                              \
        .a``_arready(b``_arready),                              \
        .a``_rdata(b``_rdata),                                  \
        .a``_rresp(b``_rresp),                                  \
        .a``_rvalid(b``_rvalid),                                \
        .a``_rready(b``_rready)

`define SB_AXIL_M(mod, signal, queue, dw, aw)                   \
    sb_axil_m #(                                                \
        .DATA_WIDTH(dw),                                        \
        .ADDR_WIDTH(aw)                                         \
    ) mod (                                                     \
        .clk(clk),                                              \
        .m_axil_awaddr(signal``_awaddr),                        \
        .m_axil_awprot(signal``_awprot),                        \
        .m_axil_awvalid(signal``_awvalid),                      \
        .m_axil_awready(signal``_awready),                      \
        .m_axil_wdata(signal``_wdata),                          \
        .m_axil_wstrb(signal``_wstrb),                          \
        .m_axil_wvalid(signal``_wvalid),                        \
        .m_axil_wready(signal``_wready),                        \
        .m_axil_bresp(signal``_bresp),                          \
        .m_axil_bvalid(signal``_bvalid),                        \
        .m_axil_bready(signal``_bready),                        \
        .m_axil_araddr(signal``_araddr),                        \
        .m_axil_arprot(signal``_arprot),                        \
        .m_axil_arvalid(signal``_arvalid),                      \
        .m_axil_arready(signal``_arready),                      \
        .m_axil_rdata(signal``_rdata),                          \
        .m_axil_rresp(signal``_rresp),                          \
        .m_axil_rvalid(signal``_rvalid),                        \
        .m_axil_rready(signal``_rready)                         \
    );                                                          \
    initial begin                                               \
        /* verilator lint_off IGNOREDRETURN */                  \
        sb_axil_m_i.init(`STRINGIFY(queue));                    \
        /* verilator lint_on IGNOREDRETURN */                   \
    end

`endif
