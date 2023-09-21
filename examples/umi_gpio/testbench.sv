`default_nettype none

module testbench (
    input clk
);

    parameter integer DW=256;
    parameter integer AW=64;
    parameter integer CW=32;
    parameter integer RWIDTH=32;
    parameter integer WWIDTH=32;

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

    wire nreset;
    wire [(RWIDTH-1):0] gpio_in;
    wire [(WWIDTH-1):0] gpio_out;

    umi_gpio #(
        .DW(DW),
        .AW(AW),
        .CW(CW),
        .RWIDTH(RWIDTH),
        .WWIDTH(WWIDTH)
    ) umi_gpio_i (
        .*
    );

    reg [7:0] nreset_vec = 8'h00;
    always @(posedge clk) begin
        nreset_vec <= {nreset_vec[6:0], 1'b1};
    end

    assign nreset = nreset_vec[7];

    // operations

    assign gpio_in[ 7:0] = gpio_out[ 7:0] + 8'd12;
    assign gpio_in[15:8] = gpio_out[15:8] - 8'd34;

    // Initialize UMI

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        rx_i.init("client2rtl.q");
        tx_i.init("rtl2client.q");
        /* verilator lint_on IGNOREDRETURN */
    end

    // VCD

    initial begin
        if ($test$plusargs("trace")) begin
            $dumpfile("testbench.vcd");
            $dumpvars(0, testbench);
        end
    end

    // auto-stop

    auto_stop_sim auto_stop_sim_i (.clk(clk));

endmodule

`default_nettype wire
