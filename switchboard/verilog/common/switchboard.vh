// Swithboard utility macros.

// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`ifndef SWITCHBOARD_VH_
`define SWITCHBOARD_VH_

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
`endif
