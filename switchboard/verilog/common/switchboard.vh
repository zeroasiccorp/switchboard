// Swithboard utility macros.

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`ifndef SWITCHBOARD_VH_
`define SWITCHBOARD_VH_

`define SB_UMI_WIRES(signal, dw, cw, aw)                        \
    wire signal``_valid;                                        \
    wire [((cw)-1): 0] signal``_cmd;                            \
    wire [((aw)-1): 0] signal``_dstaddr;                        \
    wire [((aw)-1): 0] signal``_srcaddr;                        \
    wire [((dw)-1): 0] signal``_data;                           \
    wire signal``_ready

// alias for SB_UMI_WIRES, keep for backwards compatibility
`define UMI_PORT_WIRES_WIDTHS(prefix, dw, cw, aw)               \
    `SB_UMI_WIRES(prefix, dw, cw, aw)

`define QUEUE_TO_UMI_SIM(mod, signal, clk_signal, dw, cw, aw)   \
    queue_to_umi_sim #(                                         \
        .DW(dw),                                                \
        .CW(cw),                                                \
        .AW(aw)                                                 \
    ) mod (                                                     \
        .clk(clk_signal),                                       \
        .data(signal``_data),                                   \
        .srcaddr(signal``_srcaddr),                             \
        .dstaddr(signal``_dstaddr),                             \
        .cmd(signal``_cmd),                                     \
        .ready(signal``_ready),                                 \
        .valid(signal``_valid)                                  \
    )

`define UMI_TO_QUEUE_SIM(mod, signal, clk_signal, dw, cw, aw)   \
    umi_to_queue_sim #(                                         \
        .DW(dw),                                                \
        .CW(cw),                                                \
        .AW(aw)                                                 \
    ) mod (                                                     \
        .clk(clk_signal),                                       \
        .data(signal``_data),                                   \
        .srcaddr(signal``_srcaddr),                             \
        .dstaddr(signal``_dstaddr),                             \
        .cmd(signal``_cmd),                                     \
        .ready(signal``_ready),                                 \
        .valid(signal``_valid)                                  \
    )

`define SB_UMI_CONNECT(a, b)                                    \
    .a``_valid(b``_valid),                                      \
    .a``_cmd(b``_cmd),                                          \
    .a``_dstaddr(b``_dstaddr),                                  \
    .a``_srcaddr(b``_srcaddr),                                  \
    .a``_data(b``_data),                                        \
    .a``_ready(b``_ready)

`define SWITCHBOARD_SIM_PORT(prefix, dw)                        \
    `SB_UMI_WIRES(prefix``_req, dw, 32, 64);                    \
    `SB_UMI_WIRES(prefix``_resp, dw, 32, 64);                   \
                                                                \
    initial begin                                               \
        /* verilator lint_off IGNOREDRETURN */                  \
        prefix``_rx.init($sformatf("%s_req.q", `"prefix`"));    \
        prefix``_tx.init($sformatf("%s_resp.q", `"prefix`"));   \
        /* verilator lint_on IGNOREDRETURN */                   \
    end                                                         \
                                                                \
    `QUEUE_TO_UMI_SIM(                                          \
        prefix``_rx, prefix``_req, clk, dw, 32, 64);            \
                                                                \
    `UMI_TO_QUEUE_SIM(                                          \
        prefix``_tx, prefix``_resp, clk, dw, 32, 64)

`define SB_WIRES(signal, dw)                                    \
    wire [((dw)-1):0] signal``_data;                            \
    wire [31:0] signal``_dest;                                  \
    wire signal``_last;                                         \
    wire signal``_valid;                                        \
    wire signal``_ready

`define SB_TO_QUEUE_SIM(mod, signal, clk_signal, dw)            \
    sb_to_queue_sim #(                                          \
        .DW(dw)                                                 \
    ) mod (                                                     \
        .clk(clk_signal),                                       \
        .data(signal``_data),                                   \
        .dest(signal``_dest),                                   \
        .last(signal``_last),                                   \
        .ready(signal``_ready),                                 \
        .valid(signal``_valid)                                  \
    )

`define QUEUE_TO_SB_SIM(mod, signal, clk_signal, dw)            \
    queue_to_sb_sim #(                                          \
        .DW(dw)                                                 \
    ) mod (                                                     \
        .clk(clk_signal),                                       \
        .data(signal``_data),                                   \
        .dest(signal``_dest),                                   \
        .last(signal``_last),                                   \
        .ready(signal``_ready),                                 \
        .valid(signal``_valid)                                  \
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
    wire                  signal``_rready

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

`define SB_AXIL_M(mod, signal, clk_signal, dw, aw)              \
    sb_axil_m #(                                                \
        .DATA_WIDTH(dw),                                        \
        .ADDR_WIDTH(aw)                                         \
    ) mod (                                                     \
        .clk(clk_signal),                                       \
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
    )

`define SB_AXI_WIRES(signal, dw, aw, idw)                       \
    wire [(idw)-1:0]       signal``_awid;                       \
    wire [(aw)-1:0]        signal``_awaddr;                     \
    wire [7:0]             signal``_awlen;                      \
    wire [2:0]             signal``_awsize;                     \
    wire [1:0]             signal``_awburst;                    \
    wire                   signal``_awlock;                     \
    wire [3:0]             signal``_awcache;                    \
    wire [2:0]             signal``_awprot;                     \
    wire                   signal``_awvalid;                    \
    wire                   signal``_awready;                    \
    wire [(dw)-1:0]        signal``_wdata;                      \
    wire [((dw)/8)-1:0]    signal``_wstrb;                      \
    wire                   signal``_wlast;                      \
    wire                   signal``_wvalid;                     \
    wire                   signal``_wready;                     \
    wire [(idw)-1:0]       signal``_bid;                        \
    wire [1:0]             signal``_bresp;                      \
    wire                   signal``_bvalid;                     \
    wire                   signal``_bready;                     \
    wire [(idw)-1:0]       signal``_arid;                       \
    wire [(aw)-1:0]        signal``_araddr;                     \
    wire [7:0]             signal``_arlen;                      \
    wire [2:0]             signal``_arsize;                     \
    wire [1:0]             signal``_arburst;                    \
    wire                   signal``_arlock;                     \
    wire [3:0]             signal``_arcache;                    \
    wire [2:0]             signal``_arprot;                     \
    wire                   signal``_arvalid;                    \
    wire                   signal``_arready;                    \
    wire [(idw)-1:0]       signal``_rid;                        \
    wire [(dw)-1:0]        signal``_rdata;                      \
    wire [1:0]             signal``_rresp;                      \
    wire                   signal``_rlast;                      \
    wire                   signal``_rvalid;                     \
    wire                   signal``_rready;

`define SB_AXI_CONNECT(a, b)                                    \
    .a``_awid(b``_awid),                                        \
    .a``_awaddr(b``_awaddr),                                    \
    .a``_awlen(b``_awlen),                                      \
    .a``_awsize(b``_awsize),                                    \
    .a``_awburst(b``_awburst),                                  \
    .a``_awlock(b``_awlock),                                    \
    .a``_awcache(b``_awcache),                                  \
    .a``_awprot(b``_awprot),                                    \
    .a``_awvalid(b``_awvalid),                                  \
    .a``_awready(b``_awready),                                  \
    .a``_wdata(b``_wdata),                                      \
    .a``_wstrb(b``_wstrb),                                      \
    .a``_wlast(b``_wlast),                                      \
    .a``_wvalid(b``_wvalid),                                    \
    .a``_wready(b``_wready),                                    \
    .a``_bid(b``_bid),                                          \
    .a``_bresp(b``_bresp),                                      \
    .a``_bvalid(b``_bvalid),                                    \
    .a``_bready(b``_bready),                                    \
    .a``_arid(b``_arid),                                        \
    .a``_araddr(b``_araddr),                                    \
    .a``_arlen(b``_arlen),                                      \
    .a``_arsize(b``_arsize),                                    \
    .a``_arburst(b``_arburst),                                  \
    .a``_arlock(b``_arlock),                                    \
    .a``_arcache(b``_arcache),                                  \
    .a``_arprot(b``_arprot),                                    \
    .a``_arvalid(b``_arvalid),                                  \
    .a``_arready(b``_arready),                                  \
    .a``_rid(b``_rid),                                          \
    .a``_rdata(b``_rdata),                                      \
    .a``_rresp(b``_rresp),                                      \
    .a``_rlast(b``_rlast),                                      \
    .a``_rvalid(b``_rvalid),                                    \
    .a``_rready(b``_rready)

`define SB_AXI_M(mod, signal, clk_signal, dw, aw, idw)          \
    sb_axi_m #(                                                 \
        .DATA_WIDTH(dw),                                        \
        .ADDR_WIDTH(aw),                                        \
        .ID_WIDTH(idw)                                          \
    ) mod (                                                     \
        .clk(clk_signal),                                       \
        .m_axi_awid(signal``_awid),                             \
        .m_axi_awaddr(signal``_awaddr),                         \
        .m_axi_awlen(signal``_awlen),                           \
        .m_axi_awsize(signal``_awsize),                         \
        .m_axi_awburst(signal``_awburst),                       \
        .m_axi_awlock(signal``_awlock),                         \
        .m_axi_awcache(signal``_awcache),                       \
        .m_axi_awprot(signal``_awprot),                         \
        .m_axi_awvalid(signal``_awvalid),                       \
        .m_axi_awready(signal``_awready),                       \
        .m_axi_wdata(signal``_wdata),                           \
        .m_axi_wstrb(signal``_wstrb),                           \
        .m_axi_wlast(signal``_wlast),                           \
        .m_axi_wvalid(signal``_wvalid),                         \
        .m_axi_wready(signal``_wready),                         \
        .m_axi_bid(signal``_bid),                               \
        .m_axi_bresp(signal``_bresp),                           \
        .m_axi_bvalid(signal``_bvalid),                         \
        .m_axi_bready(signal``_bready),                         \
        .m_axi_arid(signal``_arid),                             \
        .m_axi_araddr(signal``_araddr),                         \
        .m_axi_arlen(signal``_arlen),                           \
        .m_axi_arsize(signal``_arsize),                         \
        .m_axi_arburst(signal``_arburst),                       \
        .m_axi_arlock(signal``_arlock),                         \
        .m_axi_arcache(signal``_arcache),                       \
        .m_axi_arprot(signal``_arprot),                         \
        .m_axi_arvalid(signal``_arvalid),                       \
        .m_axi_arready(signal``_arready),                       \
        .m_axi_rid(signal``_rid),                               \
        .m_axi_rdata(signal``_rdata),                           \
        .m_axi_rresp(signal``_rresp),                           \
        .m_axi_rlast(signal``_rlast),                           \
        .m_axi_rvalid(signal``_rvalid),                         \
        .m_axi_rready(signal``_rready)                          \
    )

`endif
