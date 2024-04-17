// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`include "switchboard.vh"

module testbench (
    `ifdef VERILATOR
        input clk
    `endif
);
    `ifndef VERILATOR
        `SB_CREATE_CLOCK(clk)
    `endif

    localparam integer DW=256;

    // SB RX port

    `SB_WIRES(to_rtl, DW);
    `QUEUE_TO_SB_SIM(to_rtl, DW);

    // SB TX port

    `SB_WIRES(from_rtl, DW);
    `SB_TO_QUEUE_SIM(from_rtl, DW);

    // loopback with data modification (add "1" to data)

    genvar i;
    generate
        for (i=0; i<(DW/8); i=i+1) begin
            assign from_rtl_data[(i*8) +: 8] = to_rtl_data[(i*8) +: 8] + 8'd1;
        end
    endgenerate

    assign from_rtl_dest = to_rtl_dest;
    assign from_rtl_last = to_rtl_last;
    assign from_rtl_valid = to_rtl_valid;
    assign to_rtl_ready = from_rtl_ready;

    // end simulation after receiving a packet of all 1's

    always @(posedge clk) begin
        if (to_rtl_valid && ((&to_rtl_data) == 1'b1)) begin
            $finish;
        end
    end

    // Waveforms

    `SB_SETUP_PROBES

endmodule
