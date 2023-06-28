`default_nettype none

module testbench (
    input clk
);

    parameter integer DW=256;
    parameter integer AW=64;
    parameter integer CW=32;

    // UMI Input
    wire umi_in_valid;
    wire [CW-1:0] umi_in_cmd;
    wire [AW-1:0] umi_in_dstaddr;
    wire [AW-1:0] umi_in_srcaddr;
    wire [DW-1:0] umi_in_data;
    wire umi_in_ready;

    // UMI Output
    wire          umi_resp_out_valid;
    wire [CW-1:0] umi_resp_out_cmd;
    wire [AW-1:0] umi_resp_out_dstaddr;
    wire [AW-1:0] umi_resp_out_srcaddr;
    wire [DW-1:0] umi_resp_out_data;
    wire          umi_resp_out_ready;

    // UMI Output
    wire          umi_req_out_valid;
    wire [CW-1:0] umi_req_out_cmd;
    wire [AW-1:0] umi_req_out_dstaddr;
    wire [AW-1:0] umi_req_out_srcaddr;
    wire [DW-1:0] umi_req_out_data;
    wire          umi_req_out_ready;

    umi_splitter umi_splitter_i (
        .*
    );

    umi_rx_sim rx (
        .clk(clk),
        .data(umi_in_data),
        .srcaddr(umi_in_srcaddr),
        .dstaddr(umi_in_dstaddr),
        .cmd(umi_in_cmd),
        .ready(umi_in_ready),
        .valid(umi_in_valid)
    );

    umi_tx_sim tx0 (
        .clk(clk),
        .data(umi_resp_out_data),
        .srcaddr(umi_resp_out_srcaddr),
        .dstaddr(umi_resp_out_dstaddr),
        .cmd(umi_resp_out_cmd),
        .ready(umi_resp_out_ready),
        .valid(umi_resp_out_valid)
    );

    umi_tx_sim tx1 (
        .clk(clk),
        .data(umi_req_out_data),
        .srcaddr(umi_req_out_srcaddr),
        .dstaddr(umi_req_out_dstaddr),
        .cmd(umi_req_out_cmd),
        .ready(umi_req_out_ready),
        .valid(umi_req_out_valid)
    );

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx.init("in.q");
        tx0.init("out0.q");
        tx1.init("out1.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // VCD

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.fst");
            $dumpvars(0, testbench);
        end
    end

    // auto-stop

    auto_stop_sim auto_stop_sim_i (.clk(clk));

endmodule

`default_nettype wire
