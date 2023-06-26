module testbench (
    `ifndef __ICARUS__
        input clk
    `endif
);
    // clock

    `ifdef __ICARUS__

        reg clk;
        always begin
            clk = 1'b0;
            #5;
            clk = 1'b1;
            #5;
        end

    `endif

    // SB RX port

    wire [255:0] sb_rx_data;
    wire [31:0] sb_rx_dest;
    wire sb_rx_last;
    wire sb_rx_valid;
    wire sb_rx_ready;

    // SB TX port

    wire [255:0] sb_tx_data;
    wire [31:0] sb_tx_dest;
    wire sb_tx_last;
    wire sb_tx_valid;
    wire sb_tx_ready;

    sb_rx_sim #(
        .DW(256)
    ) rx_i (
        .clk(clk),
        .data(sb_rx_data),  // output
        .dest(sb_rx_dest),  // output
        .last(sb_rx_last),  // output
        .ready(sb_rx_ready), // input
        .valid(sb_rx_valid)  // output
    );

    sb_tx_sim #(
        .DW(256)
    ) tx_i (
        .clk(clk),
        .data(sb_tx_data),  // input
        .dest(sb_tx_dest),  // input
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

    assign sb_tx_dest = sb_rx_dest;
    assign sb_tx_last = sb_rx_last;
    assign sb_tx_valid = sb_rx_valid;
    assign sb_rx_ready = sb_tx_ready;

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("client2rtl.q");
        tx_i.init("rtl2client.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // VCD

    initial begin
        $dumpfile("testbench.fst");
        $dumpvars(0, testbench);
    end

    // $finish

    always @(posedge clk) begin
        if (sb_rx_valid && ((&sb_rx_data) == 1'b1)) begin
            $finish;
        end
    end

    // auto-stop

    auto_stop_sim auto_stop_sim_i (.clk(clk));

endmodule
