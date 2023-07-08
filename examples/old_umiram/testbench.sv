module testbench (
    input clk
);
    // UMI RX port

    wire [255:0] umi_rx_packet;
    wire umi_rx_valid;
    wire umi_rx_ready;

    // UMI TX port

    wire [255:0] umi_tx_packet;
    wire umi_tx_valid;
    wire umi_tx_ready;

    old_umi_rx_sim rx_i (
        .clk(clk),
        .packet(umi_rx_packet), // output
        .ready(umi_rx_ready), // input
        .valid(umi_rx_valid) // output
    );

    old_umi_tx_sim tx_i (
        .clk(clk),
        .packet(umi_tx_packet), // input
        .ready(umi_tx_ready), // output
        .valid(umi_tx_valid) // input
    );

    wire stop_valid;
    old_umi_rx_sim stop_i (
        .clk(clk),
        .packet(),
        .ready(1'b1),
        .valid(stop_valid)
    );

    // instantiate module with UMI ports

    umiram ram_i (
        .*
    );


    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("rx.q");
        tx_i.init("tx.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // VCD
    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

endmodule
