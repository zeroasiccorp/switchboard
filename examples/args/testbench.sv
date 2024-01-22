// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    // clock

    `ifndef VERILATOR

        reg clk;
        always begin
            clk = 1'b0;
            #5;
            clk = 1'b1;
            #5;
        end

    `endif

    integer a=0, b=0;

    initial begin
        $value$plusargs("a+%d", a);
        $value$plusargs("b+%d", b);

        $write("a: %0d\n", a);
        $write("b: %0d\n", b);

        $write("$random: %0d\n", $random);
        $write("$random: %0d\n", $random);
        $write("$random: %0d\n", $random);

        $finish;
    end

endmodule
