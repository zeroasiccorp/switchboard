module testbench (
    input clk
);
    // SB RX port

    wire [255:0] sb_rx_data;
    wire sb_rx_last;
    wire sb_rx_valid;
    wire sb_rx_ready;

    // SB TX port

    wire [255:0] sb_tx_data;
    wire sb_tx_last;
    wire sb_tx_valid;
    wire sb_tx_ready;

    sb_rx_sim rx_i (
        .clk(clk),
        .data(sb_rx_data),  // output
        .dest(),  // unused
        .last(sb_rx_last),  // output
        .ready(sb_rx_ready),  // input
        .valid(sb_rx_valid)  // output
    );

    sb_tx_sim tx_i (
        .clk(clk),
        .data(sb_tx_data),  // input
        .dest(32'd0),  // input
        .last(sb_tx_last),  // input
        .ready(sb_tx_ready), // output
        .valid(sb_tx_valid)  // input
    );

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

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init($sformatf("queue-%0d", 5557));
        tx_i.init($sformatf("queue-%0d", 5558));
        /* verilator lint_on IGNOREDRETURN */
    end

endmodule
