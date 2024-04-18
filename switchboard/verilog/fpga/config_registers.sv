// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

`ifndef VERSION_MAJOR
`define VERSION_MAJOR 0
`endif

`ifndef VERSION_MINOR
`define VERSION_MINOR 0
`endif

`define USER_REG(i) (i == 0 ? USER_0_REG : USER_1_BASE + (i - 1) * PER_USER_OFFSET)

module config_registers #(
    // can be up to 13
    parameter NUM_USER_REGS = 0,
    parameter NUM_QUEUES = 2
) (
    input wire clk,
    input wire nreset,

    input wire [31:0] s_axil_awaddr,
    input wire s_axil_awvalid,
    output wire s_axil_awready,
    input wire [31:0] s_axil_wdata,
    input wire [3:0] s_axil_wstrb,
    input wire s_axil_wvalid,
    output wire s_axil_wready,
    output wire [1:0] s_axil_bresp,
    output wire s_axil_bvalid,
    input wire s_axil_bready,
    input wire [31:0] s_axil_araddr,
    input wire s_axil_arvalid,
    output wire s_axil_arready,
    output wire [31:0] s_axil_rdata,
    output wire [1:0] s_axil_rresp,
    output wire s_axil_rvalid,
    input wire s_axil_rready,

    input wire [NUM_QUEUES-1:0] status_idle,
    output reg [NUM_QUEUES-1:0] cfg_enable = {NUM_QUEUES{1'd0}},
    output reg [NUM_QUEUES-1:0] cfg_reset = {NUM_QUEUES{1'd0}},
    output reg [NUM_QUEUES*64-1:0] cfg_base_addr,
    output reg [NUM_QUEUES*32-1:0] cfg_capacity = {NUM_QUEUES{32'd2}},
    output reg [(NUM_USER_REGS > 0 ? NUM_USER_REGS : 1)*32-1:0] cfg_user
);

    `include "sb_queue_regmap.vh"

    localparam [31:0] ID_VERSION = {16'h1234, 7'd`VERSION_MAJOR, 9'd`VERSION_MINOR};
    localparam [31:0] UNIMPLEMENTED_REG_VALUE = 32'hffff_ffff;

    wire axil_awvalid_q;
    wire [31:0] axil_awaddr_q;
    wire axil_awready_q;
    wire axil_wvalid_q;
    wire [31:0] axil_wdata_q;
    wire [3:0] axil_wstrb_q;
    wire axil_wready_q;
    wire axil_bvalid_q;
    wire [1:0] axil_bresp_q;
    wire axil_bready_q;
    wire axil_arvalid_q;
    wire [31:0] axil_araddr_q;
    wire axil_arready_q;
    wire axil_rvalid_q;
    wire [31:0] axil_rdata_q;
    wire [1:0] axil_rresp_q;
    wire axil_rready_q;

    axil_register axil_reg (
        .clk(clk),
        .rst(~nreset),
        .s_axil_awaddr  (s_axil_awaddr),
        .s_axil_awprot  (),
        .s_axil_awvalid (s_axil_awvalid),
        .s_axil_awready (s_axil_awready),
        .s_axil_wdata   (s_axil_wdata),
        .s_axil_wstrb   (s_axil_wstrb),
        .s_axil_wvalid  (s_axil_wvalid),
        .s_axil_wready  (s_axil_wready),
        .s_axil_bresp   (s_axil_bresp),
        .s_axil_bvalid  (s_axil_bvalid),
        .s_axil_bready  (s_axil_bready),
        .s_axil_araddr  (s_axil_araddr),
        .s_axil_arprot  (),
        .s_axil_arvalid (s_axil_arvalid),
        .s_axil_arready (s_axil_arready),
        .s_axil_rdata   (s_axil_rdata),
        .s_axil_rresp   (s_axil_rresp),
        .s_axil_rvalid  (s_axil_rvalid),
        .s_axil_rready  (s_axil_rready),

        .m_axil_awaddr  (axil_awaddr_q),
        .m_axil_awprot  (),
        .m_axil_awvalid (axil_awvalid_q),
        .m_axil_awready (axil_awready_q),
        .m_axil_wdata   (axil_wdata_q),
        .m_axil_wstrb   (axil_wstrb_q),
        .m_axil_wvalid  (axil_wvalid_q),
        .m_axil_wready  (axil_wready_q),
        .m_axil_bresp   (axil_bresp_q),
        .m_axil_bvalid  (axil_bvalid_q),
        .m_axil_bready  (axil_bready_q),
        .m_axil_araddr  (axil_araddr_q),
        .m_axil_arprot  (),
        .m_axil_arvalid (axil_arvalid_q),
        .m_axil_arready (axil_arready_q),
        .m_axil_rdata   (axil_rdata_q),
        .m_axil_rresp   (axil_rresp_q),
        .m_axil_rvalid  (axil_rvalid_q),
        .m_axil_rready  (axil_rready_q)
    );

    wire [31:0] reg_wr_addr;
    wire [31:0] reg_wr_data;
    wire [3:0] reg_wr_strb;
    wire reg_wr_en;

    wire [31:0] reg_rd_addr;
    reg [31:0] reg_rd_data;
    wire reg_rd_en;

    axil_reg_if reg_if (
        .clk(clk),
        .rst(~nreset),

        .s_axil_awaddr(axil_awaddr_q),
        .s_axil_awprot(),
        .s_axil_awvalid(axil_awvalid_q),
        .s_axil_awready(axil_awready_q),
        .s_axil_wdata(axil_wdata_q),
        .s_axil_wstrb(axil_wstrb_q),
        .s_axil_wvalid(axil_wvalid_q),
        .s_axil_wready(axil_wready_q),
        .s_axil_bresp(axil_bresp_q),
        .s_axil_bvalid(axil_bvalid_q),
        .s_axil_bready(axil_bready_q),
        .s_axil_araddr(axil_araddr_q),
        .s_axil_arprot(),
        .s_axil_arvalid(axil_arvalid_q),
        .s_axil_arready(axil_arready_q),
        .s_axil_rdata(axil_rdata_q),
        .s_axil_rresp(axil_rresp_q),
        .s_axil_rvalid(axil_rvalid_q),
        .s_axil_rready(axil_rready_q),

        .reg_wr_addr(reg_wr_addr),
        .reg_wr_data(reg_wr_data),
        .reg_wr_strb(reg_wr_strb),
        .reg_wr_en(reg_wr_en),
        .reg_wr_wait(1'b0),
        .reg_wr_ack(1'b1),

        .reg_rd_addr(reg_rd_addr),
        .reg_rd_en(reg_rd_en),
        .reg_rd_data(reg_rd_data),
        .reg_rd_wait(1'b0),
        .reg_rd_ack(1'b1)
    );

    // TODO: implement wstrb

    genvar i;
    generate
        for (i = 0; i < NUM_USER_REGS; i++) begin
            always @(posedge clk) begin
                if (reg_wr_en && reg_wr_addr == `USER_REG(i)) begin
                    cfg_user[i*32+:32] <= reg_wr_data;
                end
            end
        end

        for (i = 0; i < NUM_QUEUES; i++) begin
            always @(posedge clk) begin
                if (cfg_reset[i]) begin
                    cfg_base_addr[i*64+:64] <= 64'd0;
                    cfg_capacity[i*32+:32] <= 32'd2;
                    cfg_enable[i] <= 1'd0;
                    cfg_reset[i] <= 1'd0;
                end else if (reg_wr_en) begin
                    if (reg_wr_addr == BASE_ADDR_LO_REG + i * REG_OFFSET) begin
                        cfg_base_addr[i*64+:32] <= reg_wr_data;
                    end else if (reg_wr_addr == BASE_ADDR_HI_REG + i * REG_OFFSET) begin
                        cfg_base_addr[i*64+32+:32] <= reg_wr_data;
                    end else if (reg_wr_addr == CAPACITY_REG + i * REG_OFFSET) begin
                        cfg_capacity[i*32+:32] <= reg_wr_data;
                    end else if (reg_wr_addr == ENABLE_REG + i * REG_OFFSET) begin
                        cfg_enable[i] <= reg_wr_data[0];
                    end else if (reg_wr_addr == RESET_REG + i * REG_OFFSET) begin
                        cfg_reset[i] <= reg_wr_data[0];
                    end
                end
            end
        end
    endgenerate

    always @(*) begin
        reg_rd_data = UNIMPLEMENTED_REG_VALUE;
        if (reg_rd_en) begin
            if (reg_rd_addr == ID_VERSION_REG) begin
                reg_rd_data = ID_VERSION;
            end else if (reg_rd_addr == CAPABILITY_REG) begin
                reg_rd_data = 32'h0;
            end else begin
                integer i;

                for (i = 0; i < NUM_USER_REGS; i = i + 1) begin
                    if (reg_rd_addr == `USER_REG(i)) begin
                        reg_rd_data = cfg_user[i*32+:32];
                    end
                end

                for (i = 0; i < NUM_QUEUES; i = i + 1) begin
                    if (reg_rd_addr == BASE_ADDR_LO_REG + i * REG_OFFSET) begin
                        reg_rd_data = cfg_base_addr[i*64+:32];
                    end else if (reg_rd_addr == BASE_ADDR_HI_REG + i * REG_OFFSET) begin
                        reg_rd_data = cfg_base_addr[i*64+32+:32];
                    end else if (reg_rd_addr == CAPACITY_REG + i * REG_OFFSET) begin
                        reg_rd_data = cfg_capacity[i*32+:32];
                    end else if (reg_rd_addr == ENABLE_REG + i * REG_OFFSET) begin
                        reg_rd_data = {31'd0, cfg_enable[i]};
                    end else if (reg_rd_addr == RESET_REG + i * REG_OFFSET) begin
                        reg_rd_data = {31'd0, cfg_reset[i]};
                    end else if (reg_rd_addr == STATUS_REG + i * REG_OFFSET) begin
                        reg_rd_data = {31'd0, status_idle[i]};
                    end
                end
            end
        end
    end

`ifdef DEBUG
   ila_0 ILA_0 (
                   .clk    (clk),
                   .probe0 (axil_arvalid_q),
                   .probe1 ({32'd0, axil_araddr_q}),
                   .probe2 (axil_arready_q),
                   .probe3 (axil_rvalid_q),
                   .probe4 ({32'd0, axil_rdata_q}),
                   .probe5 (axil_rready_q)
                   );
`endif

endmodule

`default_nettype wire
