// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module memory_fault(
    input wire clk,
    input wire reset,

    input wire access_valid_in,
    input wire [63:0] access_addr,

    input wire [63:0] base_legal_addr,
    input wire [63:0] legal_length,

    output wire access_valid_out,
    output reg fault = 1'b0,
    output reg [63:0] fault_addr = 64'd0
);

    wire access_oob;
    assign access_oob = access_valid_in &&
                        ((access_addr < base_legal_addr) ||
                         (access_addr >= base_legal_addr + legal_length));

    assign access_valid_out = !access_oob ? access_valid_in : 1'b0;

    always @(posedge clk) begin
        if (reset) begin
            fault <= 1'b0;
            fault_addr <= 64'd0;
        end else if (access_oob) begin
            fault <= 1'b1;
            fault_addr <= access_addr;
        end
    end

endmodule

`default_nettype wire
