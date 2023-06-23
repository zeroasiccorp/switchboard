`default_nettype none

module testbench (
    input clk
);

    parameter integer DW=256;
    parameter integer AW=64;
    parameter integer CW=32;

    wire           udev_req_valid;
    wire           udev_req_ready;
    wire [CW-1:0]  udev_req_cmd;
    wire [AW-1:0]  udev_req_dstaddr;
    wire [AW-1:0]  udev_req_srcaddr;
    wire [DW-1:0]  udev_req_data;

    wire          udev_resp_valid;
    wire          udev_resp_ready;
    wire [CW-1:0] udev_resp_cmd;
    wire [AW-1:0] udev_resp_dstaddr;
    wire [AW-1:0] udev_resp_srcaddr;
    wire [DW-1:0] udev_resp_data;

    umi_rx_sim rx_i (
        .clk(clk),
        .data(udev_req_data),
        .srcaddr(udev_req_srcaddr),
        .dstaddr(udev_req_dstaddr),
        .cmd(udev_req_cmd),
        .ready(udev_req_ready),
        .valid(udev_req_valid)
    );

    umi_tx_sim tx_i (
        .clk(clk),
        .data(udev_resp_data),
        .srcaddr(udev_resp_srcaddr),
        .dstaddr(udev_resp_dstaddr),
        .cmd(udev_resp_cmd),
        .ready(udev_resp_ready),
        .valid(udev_resp_valid)
    );

    wire stop_valid;
    umi_rx_sim stop_i (
        .clk(clk),
        .data(),
        .srcaddr(),
        .dstaddr(),
        .cmd(),
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
        rx_i.init("queue-5555");
        tx_i.init("queue-5556");
        stop_i.init("queue-5557");
        /* verilator lint_on IGNOREDRETURN */
    end

    // VCD
    initial begin
        $dumpfile("testbench.vcd");
        $dumpvars(0, testbench);
    end

    // $finish
    always @(posedge clk) begin
        if (stop_valid) begin
            $finish;
        end
    end

endmodule

`default_nettype wire
