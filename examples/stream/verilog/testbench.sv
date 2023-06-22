module testbench (
    input clk
);
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
        .DW(256),
        .VALID_MODE_DEFAULT(0)
    ) rx_i (
        .clk(clk),
        .data(sb_rx_data),  // output
        .dest(sb_rx_dest),  // output
        .last(sb_rx_last),  // output
        .ready(sb_rx_ready), // input
        .valid(sb_rx_valid)  // output
    );

    sb_tx_sim #(
        .DW(256),
        .READY_MODE_DEFAULT(0)
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
        assign sb_tx_data[63:0] = sb_rx_data[63:0] + 64'd42;
    endgenerate

    assign sb_tx_dest = sb_rx_dest;
    assign sb_tx_last = sb_rx_last;
    assign sb_tx_valid = sb_rx_valid;
    assign sb_rx_ready = sb_tx_ready;

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("queue-5555");
        tx_i.init("queue-5556");
        /* verilator lint_on IGNOREDRETURN */
    end

    // VCD

    initial begin
        $dumpfile("testbench.vcd");
        $dumpvars(0, testbench);
    end

    // $finish

    always @(posedge clk) begin
        if (sb_rx_valid && ((&sb_rx_data) == 1'b1)) begin
            $finish;
        end
    end

endmodule
