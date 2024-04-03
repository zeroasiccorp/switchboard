// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    `ifndef VERILATOR

        reg clk;
        always begin
            clk = 1'b0;
            #5;
            clk = 1'b1;
            #5;
        end

    `endif

    reg [7:0] rst_vec = 8'hFF;

    always @(posedge clk) begin
        rst_vec <= {rst_vec[6:0], 1'b0};
    end

    wire rst;
    assign rst = rst_vec[7];

    localparam DATA_WIDTH = 32;
    localparam ADDR_WIDTH = 8;
    localparam STRB_WIDTH = (DATA_WIDTH/8);

    wire [ADDR_WIDTH-1:0] axil_awaddr;
    wire [2:0]            axil_awprot;
    wire                  axil_awvalid;
    wire                  axil_awready;
    wire [DATA_WIDTH-1:0] axil_wdata;
    wire [STRB_WIDTH-1:0] axil_wstrb;
    wire                  axil_wvalid;
    wire                  axil_wready;
    wire [1:0]            axil_bresp;
    wire                  axil_bvalid;
    wire                  axil_bready;
    wire [ADDR_WIDTH-1:0] axil_araddr;
    wire [2:0]            axil_arprot;
    wire                  axil_arvalid;
    wire                  axil_arready;
    wire [DATA_WIDTH-1:0] axil_rdata;
    wire [1:0]            axil_rresp;
    wire                  axil_rvalid;
    wire                  axil_rready;

    // Switchboard module

    sb_axil_m #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) sb_axil_m_i (
        .clk(clk),
        .m_axil_awaddr(axil_awaddr),
        .m_axil_awprot(axil_awprot),
        .m_axil_awvalid(axil_awvalid),
        .m_axil_awready(axil_awready),
        .m_axil_wdata(axil_wdata),
        .m_axil_wstrb(axil_wstrb),
        .m_axil_wvalid(axil_wvalid),
        .m_axil_wready(axil_wready),
        .m_axil_bresp(axil_bresp),
        .m_axil_bvalid(axil_bvalid),
        .m_axil_bready(axil_bready),
        .m_axil_araddr(axil_araddr),
        .m_axil_arprot(axil_arprot),
        .m_axil_arvalid(axil_arvalid),
        .m_axil_arready(axil_arready),
        .m_axil_rdata(axil_rdata),
        .m_axil_rresp(axil_rresp),
        .m_axil_rvalid(axil_rvalid),
        .m_axil_rready(axil_rready)
    );

    // DUT

    axil_ram #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) axil_ram_i (
        .clk(clk),
        .rst(rst),
        .s_axil_awaddr(axil_awaddr),
        .s_axil_awprot(axil_awprot),
        .s_axil_awvalid(axil_awvalid),
        .s_axil_awready(axil_awready),
        .s_axil_wdata(axil_wdata),
        .s_axil_wstrb(axil_wstrb),
        .s_axil_wvalid(axil_wvalid),
        .s_axil_wready(axil_wready),
        .s_axil_bresp(axil_bresp),
        .s_axil_bvalid(axil_bvalid),
        .s_axil_bready(axil_bready),
        .s_axil_araddr(axil_araddr),
        .s_axil_arprot(axil_arprot),
        .s_axil_arvalid(axil_arvalid),
        .s_axil_arready(axil_arready),
        .s_axil_rdata(axil_rdata),
        .s_axil_rresp(axil_rresp),
        .s_axil_rvalid(axil_rvalid),
        .s_axil_rready(axil_rready)
    );

    localparam VALID_ADDR_WIDTH = ADDR_WIDTH - $clog2(STRB_WIDTH);

    initial begin
        // initialize memory to zeros for easy comparison against a behavioral model
        for (int i=0; i<2**VALID_ADDR_WIDTH; i=i+1) begin
            axil_ram_i.mem[i] = 0;
        end
    end

    // Initialize Switchboard

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        sb_axil_m_i.init("axil");
        /* verilator lint_on IGNOREDRETURN */
    end

    // Waveforms

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

endmodule

`default_nettype wire
