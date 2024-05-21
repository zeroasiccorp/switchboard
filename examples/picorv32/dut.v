// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`include "switchboard.vh"

module dut #(
    parameter DW = 32,
    parameter IDW = 16,
    parameter AW = 64,
    parameter CW = 32
) (
    input clk,

    input picorv32_resetn,
    input axilite2umi_resetn,

    `SB_UMI_OUTPUT(uhost_req, DW, CW, AW),
    `SB_UMI_INPUT(uhost_resp, DW, CW, AW)
);

    // wire interfaces

    `SB_AXIL_WIRES(mem_axi, 32, 32);

    assign mem_axi_bresp = 2'b00;
    assign mem_axi_rresp = 2'b00;

    // instantiate PicoRV32

    picorv32_axi #(
        .ENABLE_MUL(1),
        .ENABLE_DIV(1),
        .ENABLE_IRQ(1),
        .ENABLE_TRACE(1),
        .COMPRESSED_ISA(0)
    ) picorv32_axi_ (
        .clk(clk),
        .resetn(picorv32_resetn),
        .trap(),

        // AW
        .mem_axi_awvalid(mem_axi_awvalid),
        .mem_axi_awready(mem_axi_awready),
        .mem_axi_awaddr(mem_axi_awaddr),
        .mem_axi_awprot(mem_axi_awprot),

        // W
        .mem_axi_wvalid(mem_axi_wvalid),
        .mem_axi_wready(mem_axi_wready),
        .mem_axi_wdata(mem_axi_wdata),
        .mem_axi_wstrb(mem_axi_wstrb),

        // B
        .mem_axi_bvalid(mem_axi_bvalid),
        .mem_axi_bready(mem_axi_bready),

        // AR
        .mem_axi_arvalid(mem_axi_arvalid),
        .mem_axi_arready(mem_axi_arready),
        .mem_axi_araddr(mem_axi_araddr),
        .mem_axi_arprot(mem_axi_arprot),

        // R
        .mem_axi_rvalid(mem_axi_rvalid),
        .mem_axi_rready(mem_axi_rready),
        .mem_axi_rdata(mem_axi_rdata),

        // pico co-processor interface (PCPI)
        .pcpi_valid(),
        .pcpi_insn(),
        .pcpi_rs1(),
        .pcpi_rs2(),
        .pcpi_wr(),
        .pcpi_rd(),
        .pcpi_wait(),
        .pcpi_ready(),

        // IRQ interface
        .irq(32'b0),
        .eoi(),

        // trace interface
        .trace_valid(),
        .trace_data()
    );

    axilite2umi #(
        .CW(CW),
        .AW(AW),
        .DW(DW),
        .IDW(IDW)
    ) axilite2umi_ (
        .clk(clk),
        .nreset(axilite2umi_resetn),

        .chipid(16'b0),
        .local_routing(16'b0),

        `SB_AXIL_CONNECT(axi, mem_axi),
        `SB_UMI_CONNECT(uhost_req, uhost_req),
        `SB_UMI_CONNECT(uhost_resp, uhost_resp)
    );

    perf_meas_sim perf_meas_sim_ (
        .clk(clk)
    );

    reg perf_init = 0;

    always @(posedge clk) begin
        if (uhost_resp_valid && uhost_resp_ready && uhost_resp_dstaddr[63:32] == 32'd0) begin
            if (!perf_init) begin
                perf_meas_sim_.init(1);
                perf_init <= 1;
            end
        end
    end

endmodule
