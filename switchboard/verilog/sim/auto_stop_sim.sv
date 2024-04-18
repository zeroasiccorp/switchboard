// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`default_nettype none

module auto_stop_sim #(
    parameter CYCLES=50000000
) (
    input clk
);

    integer i=0;

    always @(posedge clk) begin
        if (i >= CYCLES) begin
            $display("STOPPING SIMULATION");
            $finish;
        end else begin
            i <= i + 1;
        end
    end

endmodule

`default_nettype wire
