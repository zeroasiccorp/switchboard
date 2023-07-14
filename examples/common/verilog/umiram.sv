`default_nettype none

module umiram #(
    parameter integer ADDR_WIDTH=8,
    parameter integer DATA_WIDTH=32,
    parameter integer DW=256,
    parameter integer AW=64,
    parameter integer CW=32,
    parameter integer ATOMIC_WIDTH=64
) (
    input clk,

    input           udev_req_valid,
    output          udev_req_ready,
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

    wire [4:0]   req_opcode;
    wire [2:0]   req_size;
    wire [7:0]   req_len;
    wire [7:0]   req_atype;
    wire [3:0]   req_qos;
    wire [1:0]   req_prot;
    wire         req_eom;
    wire         req_eof;
    wire         req_ex;
    wire [1:0]   req_user;
    wire [18:0]  req_user_extended;
    wire [1:0]   req_err;
    wire [4:0]   req_hostid;

    /* verilator lint_off PINMISSING */
    umi_unpack umi_unpack_i (
        .packet_cmd(udev_req_cmd),
        .cmd_opcode(req_opcode),
        .cmd_size(req_size),
        .cmd_len(req_len),
        .cmd_atype(req_atype),
        .cmd_qos(req_qos),
        .cmd_prot(req_prot),
        .cmd_eom(req_eom),
        .cmd_eof(req_eof),
        .cmd_ex(req_ex),
        .cmd_user(req_user),
        .cmd_user_extended(req_user_extended),
        .cmd_err(req_err),
        .cmd_hostid(req_hostid)
    );
    /* verilator lint_on PINMISSING */

    wire req_cmd_read;
    assign req_cmd_read = (req_opcode == UMI_REQ_READ) ? 1'b1 : 1'b0;

    wire req_cmd_write;
    assign req_cmd_write = (req_opcode == UMI_REQ_WRITE) ? 1'b1 : 1'b0;

    wire req_cmd_posted;
    assign req_cmd_posted = (req_opcode == UMI_REQ_POSTED) ? 1'b1 : 1'b0;

    wire req_cmd_atomic;
    assign req_cmd_atomic = (req_opcode == UMI_REQ_ATOMIC) ? 1'b1 : 1'b0;

    // form outgoing packet (which can only be a read response)

    /* verilator lint_off WIDTH */
    localparam [2:0] UMI_SIZE = $clog2(DATA_WIDTH/8);
    /* verilator lint_on WIDTH */

    reg [4:0]   resp_opcode;
    reg [2:0]   resp_size;
    reg [7:0]   resp_len;
    reg [7:0]   resp_atype;
    reg [3:0]   resp_qos;
    reg [1:0]   resp_prot;
    reg         resp_eom;
    reg         resp_eof;
    reg         resp_ex;
    reg [1:0]   resp_user;
    reg [18:0]  resp_user_extended;
    reg [1:0]   resp_err;
    reg [4:0]   resp_hostid;

    umi_pack umi_pack_i (
        .cmd_opcode(resp_opcode),
        .cmd_size(resp_size),
        .cmd_len(resp_len),
        .cmd_atype(resp_atype),
        .cmd_prot(resp_prot),
        .cmd_qos(resp_qos),
        .cmd_eom(resp_eom),
        .cmd_eof(resp_eof),
        .cmd_user(resp_user),
        .cmd_err(resp_err),
        .cmd_ex(resp_ex),
        .cmd_hostid(resp_hostid),
        .cmd_user_extended(resp_user_extended),
        .packet_cmd(udev_resp_cmd)
    );

    // main logic

    // note: using an unpacked array of bytes seemed like a more
    // natural approach, but didn't seem to be supported by Verilator
    // as used below (for loop of non-blocking assignments), so I
    // fell back to using a packed array.  SGH 6/23/23
    reg [((2**ADDR_WIDTH)*8-1):0] mem;

    wire [15:0] nbytes;
    assign nbytes = ({8'd0, req_cmd_atomic ? 8'd0 : req_len} + 16'd1)*(16'd1<<{13'd0, req_size});

    assign udev_req_ready = !(udev_resp_valid && (!udev_resp_ready));

    integer i;

    function [ATOMIC_WIDTH-1:0] atomic_op(input [ATOMIC_WIDTH-1:0] a,
        input [ATOMIC_WIDTH-1:0] b, input [3:0] size, input [7:0] atype);

        integer nbits;
        integer nshift;
        reg signed [ATOMIC_WIDTH-1:0] aval;
        reg [ATOMIC_WIDTH-1:0] avalu;
        reg signed [ATOMIC_WIDTH-1:0] bval;
        reg [ATOMIC_WIDTH-1:0] bvalu;

        nbits = (32'd1 << {28'd0, size}) << 32'd3;
        if (nbits > ATOMIC_WIDTH) begin
            nbits = ATOMIC_WIDTH;
        end

        nshift = ATOMIC_WIDTH - nbits;

        avalu = (a << nshift) >> nshift;
        bvalu = (b << nshift) >> nshift;

        aval = (a <<< nshift) >>> nshift;
        bval = (b <<< nshift) >>> nshift;

        if (atype == UMI_REQ_ATOMICSWAP) begin
            atomic_op = bval;
        end else if (atype == UMI_REQ_ATOMICADD) begin
            atomic_op = aval + bval;
        end else if (atype == UMI_REQ_ATOMICAND) begin
            atomic_op = aval & bval;
        end else if (atype == UMI_REQ_ATOMICOR) begin
            atomic_op = aval | bval;
        end else if (atype == UMI_REQ_ATOMICXOR) begin
            atomic_op = aval ^ bval;
        end else if (atype == UMI_REQ_ATOMICMIN) begin
            atomic_op = (aval <= bval) ? aval : bval;
        end else if (atype == UMI_REQ_ATOMICMAX) begin
            atomic_op = (aval >= bval) ? aval : bval;
        end else if (atype == UMI_REQ_ATOMICMINU) begin
            atomic_op = (avalu <= bvalu) ? avalu : bvalu;
        end else if (atype == UMI_REQ_ATOMICMAXU) begin
            atomic_op = (avalu >= bvalu) ? avalu : bvalu;
        end else begin
            atomic_op = '0;
        end
    endfunction

    reg [ATOMIC_WIDTH-1:0] a_atomic;
    reg [ATOMIC_WIDTH-1:0] b_atomic;
    reg [ATOMIC_WIDTH-1:0] y_atomic;

    always @(posedge clk) begin
        if (udev_req_valid && udev_req_ready) begin
            if (req_cmd_posted || req_cmd_write) begin
                for (i=0; i<nbytes; i=i+1) begin
                    mem[(i+udev_req_dstaddr)*8 +: 8] <= udev_req_data[i*8 +: 8];
                end
                if (req_cmd_write) begin
                    resp_opcode <= UMI_RESP_WRITE;
                    udev_resp_valid <= 1'b1;
                end
            end else if (req_cmd_read || req_cmd_atomic) begin
                for (i=0; i<nbytes; i=i+1) begin
                    udev_resp_data[i*8 +: 8] <= mem[(i+udev_req_dstaddr)*8 +: 8];
                    if (req_cmd_atomic) begin
                        // blocking assignment
                        a_atomic[i*8 +: 8] = mem[(i+udev_req_dstaddr)*8 +: 8];
                    end
                end
                if (req_cmd_atomic) begin
                    for (i=0; i<nbytes; i=i+1) begin
                        // blocking assignment
                        b_atomic[i*8 +: 8] = udev_req_data[i*8 +: 8];
                    end
                    // blocking assignment
                    y_atomic = atomic_op(a_atomic, b_atomic, req_size, req_atype);
                    for (i=0; i<nbytes; i=i+1) begin
                        mem[(i+udev_req_dstaddr)*8 +: 8] <= y_atomic[i*8 +: 8];
                    end
                end
                resp_opcode <= UMI_RESP_READ;
                udev_resp_valid <= 1'b1;
            end

            // pass through data
            resp_size <= req_size;
            resp_len <= req_cmd_atomic ? 8'd0 : req_len;
            resp_atype <= req_atype;
            resp_prot <= req_prot;
            resp_qos <= req_qos;
            resp_eom <= req_eom;
            resp_eof <= req_eof;
            resp_user <= req_user;
            resp_err <= req_err;
            resp_ex <= req_ex;
            resp_hostid <= req_hostid;
            resp_user_extended <= req_user_extended;
            udev_resp_dstaddr <= udev_req_srcaddr;
        end else if (udev_resp_valid && udev_resp_ready) begin
            udev_resp_valid <= 1'b0;
        end
    end

endmodule

`default_nettype wire
