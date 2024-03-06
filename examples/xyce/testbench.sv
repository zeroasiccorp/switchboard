// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    // Generate oversampling clock if not using Verilator

    `ifndef VERILATOR
        timeunit 1s;
        timeprecision 1fs;

        real period = 10e-9;
        initial begin
            $value$plusargs("period=%f", period);
        end

        reg clk;
        always begin
            clk = 1'b0;
            #(0.5 * period);
            clk = 1'b1;
            #(0.5 * period);
        end
    `endif

    // Generate a waveform to pass into the analog model

    reg in = 1'b0;
    wire out;

    integer count = 0;
    integer flips = 0;

    always @(posedge clk) begin
        if (count + 1 == 10) begin
            count <= 0;
            in <= ~in;
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

    rc rc_i (
        .in(in),
        .out(out),
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
