`default_nettype none

`timescale 1ns / 1ps

module testbench #(
    parameter integer UW = 256
) (
    input clk
);
    // TODO: connect to GPIO block
    wire nreset;
    wire error_fatal;

    // UMI port for testbench control
    wire umi_tb_in_valid;
    wire [(UW-1):0] umi_tb_in_packet;
    wire umi_tb_in_ready;
    wire umi_tb_out_valid;
    wire [(UW-1):0] umi_tb_out_packet;
    wire umi_tb_out_ready;

    // data interface
    wire umi1_in_valid;
    wire [(UW-1):0] umi1_in_packet;
    wire umi1_in_ready;
    wire umi1_out_valid;
    wire [(UW-1):0] umi1_out_packet;
    wire umi1_out_ready;

    // ebrick instantiation

    ebrick_core #(
        .W(1),
        .H(1)
    ) ebrick_core_i (
        // ebrick controls (per brick)
        .clk(clk),
        .nreset(nreset),
        .go(),
        .sysclk(),
        .chipletmode(),
        .chipdir(),
        .chipid(),
        .testmode(),
        // core status
        .error_fatal(),
        .initdone(),
        // scan interface
        .test_se(),
        .test_si(),
        .test_so(),
        // control interface
        .umi0_in_valid(),
        .umi0_in_packet(),
        .umi0_in_ready(),
        .umi0_out_valid(),
        .umi0_out_packet(),
        .umi0_out_ready(),
        // data interface
        .umi1_in_valid(umi1_in_valid),
        .umi1_in_packet(umi1_in_packet),
        .umi1_in_ready(umi1_in_ready),
        .umi1_out_valid(umi1_out_valid),
        .umi1_out_packet(umi1_out_packet),
        .umi1_out_ready(umi1_out_ready),
        // 2D packaging interface
        .no_dout(),
        .no_oe(),
        .no_din(),
        .so_dout(),
        .so_oe(),
        .so_din(),
        .ea_dout(),
        .ea_oe(),
        .ea_din(),
        .we_dout(),
        .we_oe(),
        .we_din(),
        // analog IO pass through (analog, digital, supply)
        .so_aio(),
        .no_aio(),
        .ea_aio(),
        .we_aio(),
        // free form pass through signals
        .no_pt(),
        .so_pt(),
        .ea_pt(),
        .we_pt(),
        // supplies
        .vss(),
        .vdd(),
        .vddx(),
        .vdda(),
        .vddio()
    );

    // GPIO block instantiation

    wire [31:0] gpio_in;
    wire [31:0] gpio_out;

    assign gpio_in = {31'b0, error_fatal};
    assign nreset = gpio_out[0];

    umi_gpio #(
        .WWIDTH(32),
        .RWIDTH(32)
    ) umi_gpio_i (
        // clock and reset
        .clk(clk),
        .rst(),

        // GPIO interface
        .gpio_in(gpio_in),
        .gpio_out(gpio_out),

        // inbound UMI packet
        .umi_in_valid(umi_tb_in_valid),
        .umi_in_packet(umi_tb_in_packet),
        .umi_in_ready(umi_tb_in_ready),

        // outbound UMI packet
        .umi_out_valid(umi_tb_out_valid),
        .umi_out_packet(umi_tb_out_packet),
        .umi_out_ready(umi_tb_out_ready)
    );

    // umi1

    old_umi_rx_sim umi1_rx (
        .clk(clk),
        .packet(umi1_in_packet),
        .ready(umi1_in_ready),
        .valid(umi1_in_valid)
    );

    old_umi_tx_sim umi1_tx (
        .clk(clk),
        .packet(umi1_out_packet),
        .ready(umi1_out_ready),
        .valid(umi1_out_valid)
    );

    // umi_tb

    old_umi_rx_sim umi_tb_rx (
        .clk(clk),
        .packet(umi_tb_in_packet),
        .ready(umi_tb_in_ready),
        .valid(umi_tb_in_valid)
    );

    old_umi_tx_sim umi_tb_tx (
        .clk(clk),
        .packet(umi_tb_out_packet),
        .ready(umi_tb_out_ready),
        .valid(umi_tb_out_valid)
    );

    // initialization

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        umi1_rx.init("queue-5555");
        umi1_tx.init("queue-5556");
        umi_tb_rx.init("queue-5557");
        umi_tb_tx.init("queue-5558");
        /* verilator lint_on IGNOREDRETURN */
    end

    // check for a fatal error

    always @(posedge clk) begin
        if (nreset && error_fatal) begin
            $display("fatal error");
            $stop;
        end
    end

endmodule // testbench

`default_nettype wire
