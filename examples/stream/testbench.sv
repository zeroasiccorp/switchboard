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

    `SB_WIRES(sb_rx, DW);
    `QUEUE_TO_SB_SIM(sb_rx, DW, "client2rtl.q");

    // SB TX port

    `SB_WIRES(sb_tx, DW);
    `SB_TO_QUEUE_SIM(sb_tx, DW, "rtl2client.q");

    // custom modification of packet

    genvar i;
    generate
        assign sb_tx_data[63:0] = sb_rx_data[63:0] + 64'd42;
    endgenerate

    assign sb_tx_dest = sb_rx_dest;
    assign sb_tx_last = sb_rx_last;
    assign sb_tx_valid = sb_rx_valid;
    assign sb_rx_ready = sb_tx_ready;

    // Waveforms

    `SB_SETUP_PROBES

    // $finish

    always @(posedge clk) begin
        if (sb_rx_valid && ((&sb_rx_data) == 1'b1)) begin
            $finish;
        end
    end

endmodule
