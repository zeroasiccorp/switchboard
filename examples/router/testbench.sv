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
    `QUEUE_TO_SB_SIM(sb_rx, DW, "queue-5557");

    // SB TX port

    `SB_WIRES(sb_tx, DW);
    `SB_TO_QUEUE_SIM(sb_tx, DW, "queue-5558");

    // custom modification of packet

    genvar i;
    generate
        for (i=0; i<32; i=i+1) begin
            assign sb_tx_data[(i*8) +: 8] = sb_rx_data[(i*8) +: 8] + 8'd1;
        end
    endgenerate

    assign sb_tx_last = sb_rx_last;
    assign sb_tx_valid = sb_rx_valid;
    assign sb_rx_ready = sb_tx_ready;

    // Waveforms

    `SB_SETUP_PROBES();

endmodule
