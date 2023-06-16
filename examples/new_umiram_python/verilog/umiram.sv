`default_nettype none

module umiram #(
    parameter integer ADDR_WIDTH=8,
    parameter integer DATA_WIDTH=32,
    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32
) (
    input clk,

    input           udev_req_valid,
    output reg      udev_req_ready=1'b0,
    input  [CW-1:0] udev_req_cmd,
    input  [AW-1:0] udev_req_dstaddr,
    input  [AW-1:0] udev_req_srcaddr,
    input  [DW-1:0] udev_req_data,

    output reg          udev_resp_valid=1'b0,
    input               udev_resp_ready,
    output     [CW-1:0] udev_resp_cmd,
    output reg [AW-1:0] udev_resp_dstaddr='d0,
    output     [AW-1:0] udev_resp_srcaddr,
    output     [DW-1:0] udev_resp_data
);

    `include "umi_messages.vh"

    // interpret incoming packet

    wire [4:0] req_opcode;
    wire req_cmd_read;
    wire req_cmd_write;
    wire req_cmd_posted;

    /* verilator lint_off PINMISSING */
    umi_unpack umi_unpack_i (
        .packet_cmd(udev_req_cmd),
        .cmd_opcode(req_opcode)
    );
    /* verilator lint_on PINMISSING */

    assign req_cmd_read = (req_opcode == UMI_REQ_READ) ? 1'b1 : 1'b0;
    assign req_cmd_write = (req_opcode == UMI_REQ_WRITE) ? 1'b1 : 1'b0;
    assign req_cmd_posted = (req_opcode == UMI_REQ_POSTED) ? 1'b1 : 1'b0;

    // form outgoing packet (which can only be a read response)

    /* verilator lint_off WIDTH */
    localparam [2:0] UMI_SIZE = $clog2(DATA_WIDTH/8);
    /* verilator lint_on WIDTH */

    reg [4:0] resp_opcode;

    umi_pack umi_pack_i (
        .cmd_opcode(resp_opcode),
        .cmd_size(UMI_SIZE),
        .cmd_len('d0),
        .cmd_atype('d0),
        .cmd_prot('d0),
        .cmd_qos('d0),
        .cmd_eom(1'b1),
        .cmd_eof(1'b1),
        .cmd_user('d0),
        .cmd_err('d0),
        .cmd_ex('d0),
        .cmd_hostid('d0),
        .cmd_user_extended('d0),
        .packet_cmd(udev_resp_cmd)
    );

    // main logic

    reg [(DATA_WIDTH-1):0] mem[2**ADDR_WIDTH];

    always @(posedge clk) begin
        // handle receiver
        if (udev_req_valid && udev_req_ready) begin
            udev_req_ready <= 1'b0;           
        end else if (udev_req_valid) begin
            if (req_cmd_posted) begin
                mem[udev_req_dstaddr[(ADDR_WIDTH-1):0]] <= udev_req_data[(DATA_WIDTH-1):0];
                udev_req_ready <= 1'b1;
            end else if (req_cmd_write && !udev_resp_valid) begin
                mem[udev_req_dstaddr[(ADDR_WIDTH-1):0]] <= udev_req_data[(DATA_WIDTH-1):0];
                udev_resp_dstaddr <= udev_req_srcaddr;
                udev_resp_valid <= 1'b1;
                udev_req_ready <= 1'b1;
                resp_opcode <= UMI_RESP_WRITE;
            end else if (req_cmd_read && !udev_resp_valid) begin
                udev_resp_data <= {{(DW-DATA_WIDTH){1'b0}}, mem[udev_req_dstaddr[(ADDR_WIDTH-1):0]]};
                udev_resp_dstaddr <= udev_req_srcaddr;
                udev_resp_valid <= 1'b1;
                udev_req_ready <= 1'b1;
                resp_opcode <= UMI_RESP_READ;
            end
        end

        // handle transmitter
        if (udev_resp_valid && udev_resp_ready) begin
            udev_resp_valid <= 1'b0;
        end
    end

endmodule

`default_nettype wire
