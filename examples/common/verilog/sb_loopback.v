// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

`include "switchboard.vh"

module sb_loopback #(
    parameter DW=256,
    parameter [7:0] INCREMENT=1
) (
    input clk,

    `SB_INPUT(in, DW),
    `SB_OUTPUT(out, DW)
);

    // loopback with increment

    genvar i;
    generate
        for (i=0; i<(DW/8); i=i+1) begin
            assign out_data[(i*8) +: 8] = in_data[(i*8) +: 8] + INCREMENT;
        end
    endgenerate

    assign out_dest = in_dest;
    assign out_last = in_last;
    assign out_valid = in_valid;
    assign in_ready = out_ready;

endmodule

`default_nettype wire
