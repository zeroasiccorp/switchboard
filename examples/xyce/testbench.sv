// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    `ifndef VERILATOR
        `SB_CREATE_CLOCK(clk)
    `endif

    // Generate a waveform to pass into the analog model

    reg a = 1'b0;
    reg [1:0] b = 2'd1;

    integer count = 0;
    integer flips = 0;

    always @(posedge clk) begin
        if (count + 1 == 10) begin
            count <= 0;
            a <= ~a;
            b <= b + 2'd1;
            if (flips + 1 == 10) begin
                $finish;
            end else begin
                flips <= flips + 1;
            end
        end else begin
            count <= count + 1;
        end
    end

    // Instantiate analog model

    wire y;
    wire [1:0] z;

    mycircuit mycircuit_i (
        .a(a),
        .b(b),
        .y(y),
        .z(z),
        .SB_CLK(clk)
    );

    // Waveform probing

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

endmodule
