// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module funcs (
    input [7:0] a,
    input [7:0] b,
    output [7:0] c,
    output [7:0] d,
    input [127:0] e,
    output [127:0] f,
    output [127:0] g,
    input h,
    input i,
    output j,
    output k,
    output l,
    input [7:0] m,
    input [7:0] n,
    output [7:0] o,
    input p,
    output q
);

    assign c = a + 8'd12;
    assign d = b - 8'd34;
    assign f = e;
    assign g = ~e;
    assign j = h ^ i;
    assign k = h & i;
    assign o = m + n;
    assign q = p;

endmodule

`default_nettype wire
