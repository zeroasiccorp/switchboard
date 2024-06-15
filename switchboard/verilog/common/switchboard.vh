// Swithboard utility macros.

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`ifndef SWITCHBOARD_VH_
`define SWITCHBOARD_VH_

// ref: https://stackoverflow.com/a/15376637
`define STRINGIFY(x) `"x`"

`define SB_UMI_WIRES(signal, dw, cw, aw)                                                           \
    wire signal``_valid;                                                                           \
    wire [((cw)-1): 0] signal``_cmd;                                                               \
    wire [((aw)-1): 0] signal``_dstaddr;                                                           \
    wire [((aw)-1): 0] signal``_srcaddr;                                                           \
    wire [((dw)-1): 0] signal``_data;                                                              \
    wire signal``_ready

// alias for SB_UMI_WIRES, keep for backwards compatibility
`define UMI_PORT_WIRES_WIDTHS(prefix, dw, cw, aw)                                                  \
    `SB_UMI_WIRES(prefix, dw, cw, aw)

`define QUEUE_TO_UMI_SIM(signal, dw, cw, aw, file, vldmode=1, clk_signal=clk)                      \
    queue_to_umi_sim #(                                                                            \
        .VALID_MODE_DEFAULT(vldmode),                                                              \
        .DW(dw),                                                                                   \
        .CW(cw),                                                                                   \
        .AW(aw),                                                                                   \
        .FILE(file)                                                                                \
    ) signal``_sb_inst (                                                                           \
        .clk(clk_signal),                                                                          \
        .data(signal``_data),                                                                      \
        .srcaddr(signal``_srcaddr),                                                                \
        .dstaddr(signal``_dstaddr),                                                                \
        .cmd(signal``_cmd),                                                                        \
        .ready(signal``_ready),                                                                    \
        .valid(signal``_valid)                                                                     \
    )

`define UMI_TO_QUEUE_SIM(signal, dw, cw, aw, file, rdymode=1, clk_signal=clk)                      \
    umi_to_queue_sim #(                                                                            \
        .READY_MODE_DEFAULT(rdymode),                                                              \
        .DW(dw),                                                                                   \
        .CW(cw),                                                                                   \
        .AW(aw),                                                                                   \
        .FILE(file)                                                                                \
    ) signal``_sb_inst (                                                                           \
        .clk(clk_signal),                                                                          \
        .data(signal``_data),                                                                      \
        .srcaddr(signal``_srcaddr),                                                                \
        .dstaddr(signal``_dstaddr),                                                                \
        .cmd(signal``_cmd),                                                                        \
        .ready(signal``_ready),                                                                    \
        .valid(signal``_valid)                                                                     \
    )

`define SB_UMI_CONNECT(a, b)                                                                       \
    .a``_valid(b``_valid),                                                                         \
    .a``_cmd(b``_cmd),                                                                             \
    .a``_dstaddr(b``_dstaddr),                                                                     \
    .a``_srcaddr(b``_srcaddr),                                                                     \
    .a``_data(b``_data),                                                                           \
    .a``_ready(b``_ready)

`define SB_TIEOFF_UMI_INPUT(a)                                                                     \
    .a``_valid(1'b0),                                                                              \
    .a``_cmd(),                                                                                    \
    .a``_dstaddr(),                                                                                \
    .a``_srcaddr(),                                                                                \
    .a``_data(),                                                                                   \
    .a``_ready()

`define SB_TIEOFF_UMI_OUTPUT(a)                                                                    \
    .a``_valid(),                                                                                  \
    .a``_cmd(),                                                                                    \
    .a``_dstaddr(),                                                                                \
    .a``_srcaddr(),                                                                                \
    .a``_data(),                                                                                   \
    .a``_ready(1'b0)

`define SWITCHBOARD_SIM_PORT(prefix, dw, cw=32, aw=64)                                             \
    `SB_UMI_WIRES(prefix``_req, dw, cw, aw);                                                       \
    `SB_UMI_WIRES(prefix``_resp, dw, cw, aw);                                                      \
    `QUEUE_TO_UMI_SIM(prefix``_req, dw, cw, aw, `"prefix``_req.q`");                               \
    `UMI_TO_QUEUE_SIM(prefix``_resp, dw, cw, aw, `"prefix``_resp.q`")

`define SB_UMI_PORT(signal, dw, cw=32, aw=64, i, o)                                                \
    i signal``_valid,                                                                              \
    i [((cw)-1): 0] signal``_cmd,                                                                  \
    i [((aw)-1): 0] signal``_dstaddr,                                                              \
    i [((aw)-1): 0] signal``_srcaddr,                                                              \
    i [((dw)-1): 0] signal``_data,                                                                 \
    o signal``_ready

`define SB_UMI_INPUT(signal, dw, cw=32, aw=64)                                                     \
    `SB_UMI_PORT(signal, dw, cw, aw, input, output)

`define SB_UMI_OUTPUT(signal, dw, cw=32, aw=64)                                                    \
    `SB_UMI_PORT(signal, dw, cw, aw, output, input)

`define SB_WIRES(signal, dw)                                                                       \
    wire [((dw)-1):0] signal``_data;                                                               \
    wire [31:0] signal``_dest;                                                                     \
    wire signal``_last;                                                                            \
    wire signal``_valid;                                                                           \
    wire signal``_ready

`define SB_CONNECT(a, b)                                                                           \
    .a``_data(b``_data),                                                                           \
    .a``_dest(b``_dest),                                                                           \
    .a``_last(b``_last),                                                                           \
    .a``_valid(b``_valid),                                                                         \
    .a``_ready(b``_ready)

`define SB_PORT(signal, dw, i, o)                                                                  \
    i wire [((dw)-1):0] signal``_data,                                                             \
    i wire [31:0] signal``_dest,                                                                   \
    i wire signal``_last,                                                                          \
    i wire signal``_valid,                                                                         \
    o wire signal``_ready

`define SB_INPUT(signal, dw)                                                                       \
    `SB_PORT(signal, dw, input, output)

`define SB_OUTPUT(signal, dw)                                                                      \
    `SB_PORT(signal, dw, output, input)

`define SB_TO_QUEUE_SIM(signal, dw, file, rdymode=1, clk_signal=clk)                               \
    sb_to_queue_sim #(                                                                             \
        .READY_MODE_DEFAULT(rdymode),                                                              \
        .DW(dw),                                                                                   \
        .FILE(file)                                                                                \
    ) signal``_sb_inst (                                                                           \
        .clk(clk_signal),                                                                          \
        .data(signal``_data),                                                                      \
        .dest(signal``_dest),                                                                      \
        .last(signal``_last),                                                                      \
        .ready(signal``_ready),                                                                    \
        .valid(signal``_valid)                                                                     \
    )

`define QUEUE_TO_SB_SIM(signal, dw, file, vldmode=1, clk_signal=clk)                               \
    queue_to_sb_sim #(                                                                             \
        .VALID_MODE_DEFAULT(vldmode),                                                              \
        .DW(dw),                                                                                   \
        .FILE(file)                                                                                \
    ) signal``_sb_inst (                                                                           \
        .clk(clk_signal),                                                                          \
        .data(signal``_data),                                                                      \
        .dest(signal``_dest),                                                                      \
        .last(signal``_last),                                                                      \
        .ready(signal``_ready),                                                                    \
        .valid(signal``_valid)                                                                     \
    )

`define SB_AXIL_WIRES(signal, dw, aw)                                                              \
    wire [((aw)-1):0]     signal``_awaddr;                                                         \
    wire [2:0]            signal``_awprot;                                                         \
    wire                  signal``_awvalid;                                                        \
    wire                  signal``_awready;                                                        \
    wire [((dw)-1):0]     signal``_wdata;                                                          \
    wire [(((dw)/8)-1):0] signal``_wstrb;                                                          \
    wire                  signal``_wvalid;                                                         \
    wire                  signal``_wready;                                                         \
    wire [1:0]            signal``_bresp;                                                          \
    wire                  signal``_bvalid;                                                         \
    wire                  signal``_bready;                                                         \
    wire [((aw)-1):0]     signal``_araddr;                                                         \
    wire [2:0]            signal``_arprot;                                                         \
    wire                  signal``_arvalid;                                                        \
    wire                  signal``_arready;                                                        \
    wire [((dw))-1:0]     signal``_rdata;                                                          \
    wire [1:0]            signal``_rresp;                                                          \
    wire                  signal``_rvalid;                                                         \
    wire                  signal``_rready

`define SB_AXIL_CONNECT(a, b)                                                                      \
        .a``_awaddr(b``_awaddr),                                                                   \
        .a``_awprot(b``_awprot),                                                                   \
        .a``_awvalid(b``_awvalid),                                                                 \
        .a``_awready(b``_awready),                                                                 \
        .a``_wdata(b``_wdata),                                                                     \
        .a``_wstrb(b``_wstrb),                                                                     \
        .a``_wvalid(b``_wvalid),                                                                   \
        .a``_wready(b``_wready),                                                                   \
        .a``_bresp(b``_bresp),                                                                     \
        .a``_bvalid(b``_bvalid),                                                                   \
        .a``_bready(b``_bready),                                                                   \
        .a``_araddr(b``_araddr),                                                                   \
        .a``_arprot(b``_arprot),                                                                   \
        .a``_arvalid(b``_arvalid),                                                                 \
        .a``_arready(b``_arready),                                                                 \
        .a``_rdata(b``_rdata),                                                                     \
        .a``_rresp(b``_rresp),                                                                     \
        .a``_rvalid(b``_rvalid),                                                                   \
        .a``_rready(b``_rready)

`define SB_AXIL(dir, signal, dw, aw, file, vldmode=1, rdymode=1, clk_signal=clk)                   \
    sb_axil_``dir #(                                                                               \
        .DATA_WIDTH(dw),                                                                           \
        .ADDR_WIDTH(aw),                                                                           \
        .VALID_MODE_DEFAULT(vldmode),                                                              \
        .READY_MODE_DEFAULT(rdymode),                                                              \
        .FILE(file)                                                                                \
    ) signal``_sb_inst (                                                                           \
        .clk(clk_signal),                                                                          \
        .dir``_axil_awaddr(signal``_awaddr),                                                       \
        .dir``_axil_awprot(signal``_awprot),                                                       \
        .dir``_axil_awvalid(signal``_awvalid),                                                     \
        .dir``_axil_awready(signal``_awready),                                                     \
        .dir``_axil_wdata(signal``_wdata),                                                         \
        .dir``_axil_wstrb(signal``_wstrb),                                                         \
        .dir``_axil_wvalid(signal``_wvalid),                                                       \
        .dir``_axil_wready(signal``_wready),                                                       \
        .dir``_axil_bresp(signal``_bresp),                                                         \
        .dir``_axil_bvalid(signal``_bvalid),                                                       \
        .dir``_axil_bready(signal``_bready),                                                       \
        .dir``_axil_araddr(signal``_araddr),                                                       \
        .dir``_axil_arprot(signal``_arprot),                                                       \
        .dir``_axil_arvalid(signal``_arvalid),                                                     \
        .dir``_axil_arready(signal``_arready),                                                     \
        .dir``_axil_rdata(signal``_rdata),                                                         \
        .dir``_axil_rresp(signal``_rresp),                                                         \
        .dir``_axil_rvalid(signal``_rvalid),                                                       \
        .dir``_axil_rready(signal``_rready)                                                        \
    )

`define SB_AXIL_M(signal, dw, aw, file, vldmode=1, rdymode=1, clk_signal=clk)                      \
    `SB_AXIL(m, signal, dw, aw, file, vldmode, rdymode, clk_signal)

`define SB_AXIL_S(signal, dw, aw, file, vldmode=1, rdymode=1, clk_signal=clk)                      \
    `SB_AXIL(s, signal, dw, aw, file, vldmode, rdymode, clk_signal)

`define SB_AXI_WIRES(signal, dw, aw, idw)                                                          \
    wire [(idw)-1:0]       signal``_awid;                                                          \
    wire [(aw)-1:0]        signal``_awaddr;                                                        \
    wire [7:0]             signal``_awlen;                                                         \
    wire [2:0]             signal``_awsize;                                                        \
    wire [1:0]             signal``_awburst;                                                       \
    wire                   signal``_awlock;                                                        \
    wire [3:0]             signal``_awcache;                                                       \
    wire [2:0]             signal``_awprot;                                                        \
    wire                   signal``_awvalid;                                                       \
    wire                   signal``_awready;                                                       \
    wire [(dw)-1:0]        signal``_wdata;                                                         \
    wire [((dw)/8)-1:0]    signal``_wstrb;                                                         \
    wire                   signal``_wlast;                                                         \
    wire                   signal``_wvalid;                                                        \
    wire                   signal``_wready;                                                        \
    wire [(idw)-1:0]       signal``_bid;                                                           \
    wire [1:0]             signal``_bresp;                                                         \
    wire                   signal``_bvalid;                                                        \
    wire                   signal``_bready;                                                        \
    wire [(idw)-1:0]       signal``_arid;                                                          \
    wire [(aw)-1:0]        signal``_araddr;                                                        \
    wire [7:0]             signal``_arlen;                                                         \
    wire [2:0]             signal``_arsize;                                                        \
    wire [1:0]             signal``_arburst;                                                       \
    wire                   signal``_arlock;                                                        \
    wire [3:0]             signal``_arcache;                                                       \
    wire [2:0]             signal``_arprot;                                                        \
    wire                   signal``_arvalid;                                                       \
    wire                   signal``_arready;                                                       \
    wire [(idw)-1:0]       signal``_rid;                                                           \
    wire [(dw)-1:0]        signal``_rdata;                                                         \
    wire [1:0]             signal``_rresp;                                                         \
    wire                   signal``_rlast;                                                         \
    wire                   signal``_rvalid;                                                        \
    wire                   signal``_rready;

`define SB_AXI_CONNECT(a, b)                                                                       \
    .a``_awid(b``_awid),                                                                           \
    .a``_awaddr(b``_awaddr),                                                                       \
    .a``_awlen(b``_awlen),                                                                         \
    .a``_awsize(b``_awsize),                                                                       \
    .a``_awburst(b``_awburst),                                                                     \
    .a``_awlock(b``_awlock),                                                                       \
    .a``_awcache(b``_awcache),                                                                     \
    .a``_awprot(b``_awprot),                                                                       \
    .a``_awvalid(b``_awvalid),                                                                     \
    .a``_awready(b``_awready),                                                                     \
    .a``_wdata(b``_wdata),                                                                         \
    .a``_wstrb(b``_wstrb),                                                                         \
    .a``_wlast(b``_wlast),                                                                         \
    .a``_wvalid(b``_wvalid),                                                                       \
    .a``_wready(b``_wready),                                                                       \
    .a``_bid(b``_bid),                                                                             \
    .a``_bresp(b``_bresp),                                                                         \
    .a``_bvalid(b``_bvalid),                                                                       \
    .a``_bready(b``_bready),                                                                       \
    .a``_arid(b``_arid),                                                                           \
    .a``_araddr(b``_araddr),                                                                       \
    .a``_arlen(b``_arlen),                                                                         \
    .a``_arsize(b``_arsize),                                                                       \
    .a``_arburst(b``_arburst),                                                                     \
    .a``_arlock(b``_arlock),                                                                       \
    .a``_arcache(b``_arcache),                                                                     \
    .a``_arprot(b``_arprot),                                                                       \
    .a``_arvalid(b``_arvalid),                                                                     \
    .a``_arready(b``_arready),                                                                     \
    .a``_rid(b``_rid),                                                                             \
    .a``_rdata(b``_rdata),                                                                         \
    .a``_rresp(b``_rresp),                                                                         \
    .a``_rlast(b``_rlast),                                                                         \
    .a``_rvalid(b``_rvalid),                                                                       \
    .a``_rready(b``_rready)

`define SB_AXI(dir, signal, dw, aw, idw, file, vldmode=1, rdymode=1, clk_signal=clk)               \
    sb_axi_``dir #(                                                                                \
        .DATA_WIDTH(dw),                                                                           \
        .ADDR_WIDTH(aw),                                                                           \
        .ID_WIDTH(idw),                                                                            \
        .VALID_MODE_DEFAULT(vldmode),                                                              \
        .READY_MODE_DEFAULT(rdymode),                                                              \
        .FILE(file)                                                                                \
    ) signal``_sb_inst (                                                                           \
        .clk(clk_signal),                                                                          \
        .dir``_axi_awid(signal``_awid),                                                            \
        .dir``_axi_awaddr(signal``_awaddr),                                                        \
        .dir``_axi_awlen(signal``_awlen),                                                          \
        .dir``_axi_awsize(signal``_awsize),                                                        \
        .dir``_axi_awburst(signal``_awburst),                                                      \
        .dir``_axi_awlock(signal``_awlock),                                                        \
        .dir``_axi_awcache(signal``_awcache),                                                      \
        .dir``_axi_awprot(signal``_awprot),                                                        \
        .dir``_axi_awvalid(signal``_awvalid),                                                      \
        .dir``_axi_awready(signal``_awready),                                                      \
        .dir``_axi_wdata(signal``_wdata),                                                          \
        .dir``_axi_wstrb(signal``_wstrb),                                                          \
        .dir``_axi_wlast(signal``_wlast),                                                          \
        .dir``_axi_wvalid(signal``_wvalid),                                                        \
        .dir``_axi_wready(signal``_wready),                                                        \
        .dir``_axi_bid(signal``_bid),                                                              \
        .dir``_axi_bresp(signal``_bresp),                                                          \
        .dir``_axi_bvalid(signal``_bvalid),                                                        \
        .dir``_axi_bready(signal``_bready),                                                        \
        .dir``_axi_arid(signal``_arid),                                                            \
        .dir``_axi_araddr(signal``_araddr),                                                        \
        .dir``_axi_arlen(signal``_arlen),                                                          \
        .dir``_axi_arsize(signal``_arsize),                                                        \
        .dir``_axi_arburst(signal``_arburst),                                                      \
        .dir``_axi_arlock(signal``_arlock),                                                        \
        .dir``_axi_arcache(signal``_arcache),                                                      \
        .dir``_axi_arprot(signal``_arprot),                                                        \
        .dir``_axi_arvalid(signal``_arvalid),                                                      \
        .dir``_axi_arready(signal``_arready),                                                      \
        .dir``_axi_rid(signal``_rid),                                                              \
        .dir``_axi_rdata(signal``_rdata),                                                          \
        .dir``_axi_rresp(signal``_rresp),                                                          \
        .dir``_axi_rlast(signal``_rlast),                                                          \
        .dir``_axi_rvalid(signal``_rvalid),                                                        \
        .dir``_axi_rready(signal``_rready)                                                         \
    )

`define SB_AXI_M(signal, dw, aw, idw, file, vldmode=1, rdymode=1, clk_signal=clk)                  \
    `SB_AXI(m, signal, dw, aw, idw, file, vldmode, rdymode, clk_signal)

`define SB_AXI_S(signal, dw, aw, idw, file, vldmode=1, rdymode=1, clk_signal=clk)                  \
    `SB_AXI(s, signal, dw, aw, idw, file, vldmode, rdymode, clk_signal)

`define SB_CREATE_CLOCK(clk_signal, period=10e-9, duty_cycle=0.5, max_rate=-1, start_delay=-1)     \
    wire clk_signal;                                                                               \
                                                                                                   \
    sb_clk_gen #(                                                                                  \
        .DEFAULT_PERIOD(period),                                                                   \
        .DEFAULT_DUTY_CYCLE(duty_cycle),                                                           \
        .DEFAULT_MAX_RATE(max_rate),                                                               \
        .DEFAULT_START_DELAY(start_delay)                                                          \
    ) clk_signal``_sb_inst (                                                                       \
        .clk(clk_signal)                                                                           \
    );

`define SB_SETUP_PROBES                                                                            \
    `ifdef SB_TRACE                                                                                \
        string dumpfile_sb_value;                                                                  \
        initial begin                                                                              \
            if ($test$plusargs("trace")) begin                                                     \
                if ($value$plusargs("dumpfile=%s", dumpfile_sb_value)) begin                       \
                    $dumpfile(dumpfile_sb_value);                                                  \
                end else begin                                                                     \
                    `ifdef SB_TRACE_FST                                                            \
                        $dumpfile("testbench.fst");                                                \
                    `else                                                                          \
                        $dumpfile("testbench.vcd");                                                \
                    `endif                                                                         \
                end                                                                                \
                $dumpvars(0, testbench);                                                           \
            end                                                                                    \
        end                                                                                        \
    `endif

`endif  // SWITCHBOARD_VH_
