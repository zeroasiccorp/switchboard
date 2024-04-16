// UMI/UART Transactor

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

// Written by Edgar E. Iglesias

`default_nettype none

module uart_xactor
  #(parameter BAUDRATE=115200,
    parameter CLK_FREQ=100 * 1000 * 1000,
    parameter DW=256,
    parameter AW=64,
    parameter CW=32
)
(
   input clk,
   input nreset,
   output umi_req_ready,
   input [CW-1:0] umi_req_cmd,
   input [DW-1:0]  umi_req_data,
   input [AW-1:0] umi_req_dstaddr,
   input [AW-1:0] umi_req_srcaddr,
   input umi_req_valid,

   input umi_resp_ready,
   output [CW-1:0] umi_resp_cmd,
   output [DW-1:0]  umi_resp_data,
   output [AW-1:0] umi_resp_dstaddr,
   output [AW-1:0] umi_resp_srcaddr,
   output umi_resp_valid,

   output tx_pad,
   input rx_pad
);
   localparam UART_DEBUG = 0;
   localparam UART_CLKDIV = (CLK_FREQ / (16 * BAUDRATE) * 16 - 1);

   localparam REG_TX  = 0;
   localparam REG_RX  = 4;
   localparam REG_SR  = 8;

   wire [AW-1:0] loc_addr;   // memory address
   wire          loc_write;  // write enable
   wire          loc_read;   // read request
   wire          loc_atomic; // atomic request
   wire [7:0]    loc_opcode; // opcode
   wire [2:0]    loc_size;   // size
   wire [7:0]    loc_len;    // len
   wire [7:0]    loc_atype;  // atomic type
   wire [DW-1:0] loc_wrdata; // data to write
   reg  [DW-1:0] loc_rddata; // data response
   wire          loc_ready;  // device is ready

   umi_endpoint #(.DW(DW))
   ep(.*,
      .udev_req_ready(umi_req_ready),
      .udev_req_cmd(umi_req_cmd),
      .udev_req_data(umi_req_data),
      .udev_req_dstaddr(umi_req_dstaddr),
      .udev_req_srcaddr(umi_req_srcaddr),
      .udev_req_valid(umi_req_valid),

      .udev_resp_ready(umi_resp_ready),
      .udev_resp_cmd(umi_resp_cmd),
      .udev_resp_data(umi_resp_data),
      .udev_resp_dstaddr(umi_resp_dstaddr),
      .udev_resp_srcaddr(umi_resp_srcaddr),
      .udev_resp_valid(umi_resp_valid));

   assign loc_ready = 1;

   wire rxfifo_full;
   wire rxfifo_empty;
   wire [7:0] rxfifo_dout;

   wire txfifo_full;
   wire txfifo_empty;

   wire [31:0] reg_sr = {16'b0,
                         6'b0, txfifo_full, txfifo_empty,
                         6'b0, rxfifo_full, rxfifo_empty};
   wire        rxfifo_read = loc_read && loc_addr == REG_RX;
   wire        txfifo_write = loc_write && loc_addr == REG_TX;

   // Reg access logic.
   always @(posedge clk or negedge nreset) begin
       if (~nreset) begin
           loc_rddata <= 0;
       end else begin
          if (loc_read) begin
             case (loc_addr)
                REG_RX: loc_rddata <= {24'b0, rxfifo_dout};
                REG_SR: loc_rddata <= reg_sr;
                default: loc_rddata <= 'hdeadbeef;
             endcase
          end
       end
   end

   // UART
   localparam STATE_START = 0;
   localparam STATE_STOP  = 8;
   localparam STATE_STOP2 = 9;

   reg [$clog2(UART_CLKDIV):0] clk_i;
   reg [$clog2(STATE_STOP):0]  rx_state;
   reg [8-1:0]                 rx_data;
   reg                         reset_sync;

   wire                        clk_en = (clk_i == 0);
   wire [8-1:0]                rx_next_data = {rx_pad, rx_data[7:1]};
   wire                        rx_next_data_en = clk_en && rx_state == STATE_STOP;

   reg tx_xmit;
   wire txfifo_read = ~tx_xmit && ~txfifo_empty;
   wire [7:0] txfifo_dout;

   la_syncfifo #(.DW(8),
      .DEPTH(80),        // FIFO Depth, can hold an 80 chars line?
      .NS(1),            // Number of power supplies
      .CHAOS(0),         // generates random full logic when set
      .CTRLW(1),         // width of asic ctrl interface
      .TESTW(1))         // width of asic test interface
      rx_fifo(
         .wr_full          (rxfifo_full),
         .rd_dout          (rxfifo_dout),
         .rd_empty         (rxfifo_empty),
         .clk              (clk),
         .nreset           (nreset),
         .vss              (1'b0),
         .vdd              (1'b1),
         .chaosmode        (1'b0),
         .ctrl             (1'b0),
         .test             (1'b0),
         .wr_en            (rx_next_data_en),
         .wr_din           (rx_next_data),
         .rd_en            (rxfifo_read));

   la_syncfifo #(.DW(8),
      .DEPTH(80),        // FIFO Depth, can hold an 80 chars line?
      .NS(1),            // Number of power supplies
      .CHAOS(0),         // generates random full logic when set
      .CTRLW(1),         // width of asic ctrl interface
      .TESTW(1))         // width of asic test interface
      tx_fifo(
         .wr_full          (txfifo_full),
         .rd_dout          (txfifo_dout),
         .rd_empty         (txfifo_empty),
         .clk              (clk),
         .nreset           (nreset),
         .vss              (1'b0),
         .vdd              (1'b1),
         .chaosmode        (1'b0),
         .ctrl             (1'b0),
         .test             (1'b0),
         .wr_en            (txfifo_write),
         .wr_din           (loc_wrdata[7:0]),
         .rd_en            (txfifo_read));

   // UART CLK
   always @(posedge clk or negedge nreset) begin
      if (~nreset) begin
         clk_i <= 0;
      end else begin
         clk_i <= clk_i + 1;
         if (clk_i == UART_CLKDIV[$clog2(UART_CLKDIV):0]) begin
            clk_i <= 0;
         end
      end
   end

   // RX logic
   always @(posedge clk or negedge nreset) begin
      if (~nreset) begin
         //$display("clkdiv old=%d new=%d", UART_CLKDIV_OLD, UART_CLKDIV);
         rx_state <= 0;
         rx_data <= 0;
         reset_sync <= 1;
      end else begin
         if (rx_pad == 1) begin
            reset_sync <= 0;
         end
         if (clk_en) begin
            if (rx_state == STATE_START) begin
               /* Wait for start bit.  */
               if (rx_pad == 0 && !reset_sync) begin
                  rx_state <= rx_state + 1;
               end
            end else if (rx_state <= 8) begin
               rx_state <= rx_state + 1;
               rx_data <= rx_next_data;
               if (rx_state == STATE_STOP) begin
                  /* STOP.  */
                  rx_state <= 0;
                  rx_data <= 0;
                  if (UART_DEBUG) begin
                     $write("%c", rx_next_data); $fflush();
                  end
               end
            end

            if (UART_DEBUG) begin
               $display("state=%d rx=%d data=%x.%x", rx_state, rx_pad, rx_data, rx_next_data);
            end
         end
      end
   end

   // TX logic
   reg [$clog2(STATE_STOP2):0] tx_state;
   reg [8-1:0]                 tx_data;

   reg tx;
   assign tx_pad = tx;
   always @(posedge clk or negedge nreset) begin
      if (~nreset) begin
         tx_state <= 0;
         tx_xmit <= 0;
         tx <= 1;
      end else begin
         if (txfifo_read) begin
            tx_xmit <= 1;
            tx_data <= txfifo_dout;
         end

         if (clk_en && tx_xmit) begin
            tx_state <= tx_state + 1;

            if (tx_state == STATE_START) begin
                tx <= 0;
            end else if (tx_state == STATE_STOP2) begin
                tx_xmit <= 0;
                tx_state <= STATE_START;
                tx <= 1;
            end else begin
                tx <= tx_data[tx_state - 1];
            end
         end
      end
   end
endmodule

`default_nettype wire
