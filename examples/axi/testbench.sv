// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

`include "switchboard.vh"

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

    // Declare AXI wires

    localparam DATA_WIDTH = 32;
    localparam ADDR_WIDTH = 8;
    localparam ID_WIDTH = 8;

    `SB_AXI_WIRES(axi, DATA_WIDTH, ADDR_WIDTH, ID_WIDTH);

    // Instantiate DUT

    wire rst;

    axi_ram #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .ID_WIDTH(ID_WIDTH)
    ) axi_ram_i (
        .clk(clk),
        .rst(rst),
        `SB_AXI_CONNECT(s_axi, axi)
    );

    // Instantiate switchboard module

    `SB_AXI_M(sb_axi_m_i, axi, DATA_WIDTH, ADDR_WIDTH, ID_WIDTH);

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        sb_axi_m_i.init("axi");
        /* verilator lint_on IGNOREDRETURN */
    end

    // Initialize RAM to zeros for easy comparison against a behavioral model

    localparam VALID_ADDR_WIDTH = ADDR_WIDTH - $clog2(DATA_WIDTH/8);

    initial begin
        for (int i=0; i<2**VALID_ADDR_WIDTH; i=i+1) begin
            axi_ram_i.mem[i] = 0;
        end
    end

    // Generate reset signal

    reg [7:0] rst_vec = 8'hFF;

    always @(posedge clk) begin
        rst_vec <= {rst_vec[6:0], 1'b0};
    end

    assign rst = rst_vec[7];

    // Set up waveform probing

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

endmodule

`default_nettype wire
