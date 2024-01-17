// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    // clock

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

    xyce_intf xyce_intf_i ();

    real in = 0.0;
    real out = 0.0;

    integer bits = 0;
    integer count = 0;
    always @(posedge clk) begin
        if (count + 1 == 10) begin
            count <= 0;
            in = 1.0 - in;
            if (bits + 1 == 10) begin
                $finish;
            end else begin
                bits <= bits + 1;
            end
        end else begin
            count <= count + 1;
        end
    end

    always @(in) begin
        xyce_intf_i.put("DAC0", in);
    end

    always @(clk) begin
        xyce_intf_i.get("ADC0", out);
    end

    // Initialize 

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        xyce_intf_i.init("rc.cir");
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
