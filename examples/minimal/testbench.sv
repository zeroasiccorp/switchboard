// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

`include "switchboard.vh"

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

    // SB RX port

    `SB_WIRES(sb_rx, 256);
    `QUEUE_TO_SB_SIM(rx_i, sb_rx, clk, 256);

    // SB TX port

    `SB_WIRES(sb_tx, 256);
    `SB_TO_QUEUE_SIM(tx_i, sb_tx, clk, 256);

    // custom modification of packet

    genvar i;
    generate
        for (i=0; i<32; i=i+1) begin
            assign sb_tx_data[(i*8) +: 8] = sb_rx_data[(i*8) +: 8] + 8'd1;
        end
    endgenerate

    assign sb_tx_dest = sb_rx_dest;
    assign sb_tx_last = sb_rx_last;
    assign sb_tx_valid = sb_rx_valid;
    assign sb_rx_ready = sb_tx_ready;

    // Initialize UMI

    initial begin
        rx_i.init("to_rtl.q");
        tx_i.init("from_rtl.q");
    end

    // Waveforms

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

    // $finish

    always @(posedge clk) begin
        if (sb_rx_valid && ((&sb_rx_data) == 1'b1)) begin
            $finish;
        end
    end

endmodule
