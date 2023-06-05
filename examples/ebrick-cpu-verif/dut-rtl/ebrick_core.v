/******************************************************************************
 * Function:  EBRICK Core Interface
 * Author:    Andreas Olofsson
 * Copyright: (c) 2022 Zero ASIC. All rights reserved.
 *
 * License: This file contains confidential and proprietary information of
 * Zero ASIC. This file may only be used in accordance with the terms and
 * conditions of a signed license agreement with Zero ASIC. All other use,
 * reproduction, or distribution of this software is strictly prohibited.
 *
 * Documentation:
 *
 * see ./README.md
 *
 * Notes:
 *
 * 1. W*H ctrl and data channels are connected to the core.
 * 2. The UMI channels are serialized as vectors to interoperated with
 *    legacy Verilog systems. A WxH grid of clink interfaces is serialized
 *    as follows: (0,0)-->(0,1)-->(1,0)-->(1,1)
 * 3. All cores must connect channle (0,0), all other channels are optional.
 * 4. Floating core outputs are not allowed.
 *
 ****************************************************************************/

`default_nettype none

`timescale 1ns / 1ps

module ebrick_core
  #(parameter TARGET = "DEFAULT", // technology target
    parameter TYPE   = "DEFAULT", // brick type target
    parameter W      = 2,         // brick width (mm) (1,2,3,4,5)
    parameter H      = 2,         // brick height (mm) (1,2,3,4,5)
    // Development Only
    parameter NGPIO  = 64,        // max gpio per clink (includes data)
    parameter NPT    = 16,        // pass-through per link
    parameter NAIO   = 8,         // analog io per clink
    parameter NCTRL  = 32,        // ctrl pins per clink
    parameter IOW    = 64,        // data signals per clink
    parameter UW     = 256,       // umi packet width
    parameter IDW    = 64,        // brick ID width
    parameter AW     = 64         // address width
    )
   (// ebrick controls (per brick)
    input 		 clk, // main clock signal
    input 		 nreset,// async active low reset
    input 		 go,// 1=start/boot core
    input [W*H-1:0] 	 sysclk, // 2nd systemclk (fpga/iosystem)
    input [1:0] 	 chipletmode,//00=150um,01=45um,10=10um,11=um
    input [1:0] 	 chipdir, // brick direction
    input [IDW-1:0] 	 chipid, // unique brick id "whoami
    input 		 testmode,
    // core status
    output 		 error_fatal, // shut down now!
    output 		 initdone, // 1 = core is fully initialized
    // scan interface
    input 		 test_se,
    input 		 test_si,
    output 		 test_so,
    // control interface
    input [W*H-1:0] 	 umi0_in_valid,
    input [W*H*UW-1:0] 	 umi0_in_packet,
    output [W*H-1:0] 	 umi0_in_ready,
    output [W*H-1:0] 	 umi0_out_valid,
    output [W*H*UW-1:0]  umi0_out_packet,
    input [W*H-1:0] 	 umi0_out_ready,
    // data interface
    input [W*H-1:0] 	 umi1_in_valid,
    input [W*H*UW-1:0] 	 umi1_in_packet,
    output [W*H-1:0] 	 umi1_in_ready,
    output [W*H-1:0] 	 umi1_out_valid,
    output [W*H*UW-1:0]  umi1_out_packet,
    input [W*H-1:0] 	 umi1_out_ready,
    // 2D packaging interface
    output [NGPIO*W-1:0] no_dout,
    output [NGPIO*W-1:0] no_oe,
    input [NGPIO*W-1:0]  no_din,
    output [NGPIO*W-1:0] so_dout,
    output [NGPIO*W-1:0] so_oe,
    input [NGPIO*W-1:0]  so_din,
    output [NGPIO*H-1:0] ea_dout,
    output [NGPIO*H-1:0] ea_oe,
    input [NGPIO*H-1:0]  ea_din,
    output [NGPIO*H-1:0] we_dout,
    output [NGPIO*H-1:0] we_oe,
    input [NGPIO*H-1:0]  we_din,
    // analog IO pass through (analog, digital, supply)
    inout [NAIO*W-1:0] 	 no_aio,
    inout [NAIO*W-1:0] 	 so_aio,
    inout [NAIO*H-1:0] 	 ea_aio,
    inout [NAIO*H-1:0] 	 we_aio,
    // free form pass through signals
    inout [NPT*W-1:0] 	 no_pt,
    inout [NPT*W-1:0] 	 so_pt,
    inout [NPT*H-1:0] 	 ea_pt,
    inout [NPT*H-1:0] 	 we_pt,
    // supplies
    input 		 vss, // ground
    input 		 vdd, //  main core supply
    input 		 vddx, // extra supply
    input [3:0] 	 vdda, // analog supply
    input [3:0] 	 vddio // io supplies
    );

    // AXI interface

    wire        mem_axi_awvalid;
    wire        mem_axi_awready;
    wire [31:0] mem_axi_awaddr;
    wire [ 2:0] mem_axi_awprot;

    wire        mem_axi_wvalid;
    wire        mem_axi_wready;
    wire [31:0] mem_axi_wdata;
    wire [ 3:0] mem_axi_wstrb;

    wire        mem_axi_bvalid;
    wire        mem_axi_bready;

    wire        mem_axi_arvalid;
    wire        mem_axi_arready;
    wire [31:0] mem_axi_araddr;
    wire [ 2:0] mem_axi_arprot;

    wire        mem_axi_rvalid;
    wire        mem_axi_rready;
    wire [31:0] mem_axi_rdata;

    // CPU

    wire cpu_axi_bready;
    wire cpu_axi_rready;

    picorv32_axi #(
        .ENABLE_MUL(1),
        .ENABLE_DIV(1),
        .ENABLE_IRQ(1),
        .ENABLE_TRACE(1),
        .COMPRESSED_ISA(0)
    ) cpu (
        .clk            (clk            ),
        .resetn         (nreset         ),
        .trap           (error_fatal    ),
        .mem_axi_awvalid(mem_axi_awvalid),
        .mem_axi_awready(mem_axi_awready),
        .mem_axi_awaddr (mem_axi_awaddr ),
        .mem_axi_awprot (mem_axi_awprot ),
        .mem_axi_wvalid (mem_axi_wvalid ),
        .mem_axi_wready (mem_axi_wready ),
        .mem_axi_wdata  (mem_axi_wdata  ),
        .mem_axi_wstrb  (mem_axi_wstrb  ),
        .mem_axi_bvalid (mem_axi_bvalid ),
        .mem_axi_bready (cpu_axi_bready ),
        .mem_axi_arvalid(mem_axi_arvalid),
        .mem_axi_arready(mem_axi_arready),
        .mem_axi_araddr (mem_axi_araddr ),
        .mem_axi_arprot (mem_axi_arprot ),
        .mem_axi_rvalid (mem_axi_rvalid ),
        .mem_axi_rready (cpu_axi_rready ),
        .mem_axi_rdata  (mem_axi_rdata  ),
        .irq            (0              ),
        // unused pins
        .trace_valid(),
        .trace_data(),
        .pcpi_insn(),
        .pcpi_rs1(),
        .pcpi_rs2(),
        .pcpi_wr(),
        .pcpi_rd(),
        .pcpi_wait(),
        .pcpi_ready(),
        .pcpi_valid(),
        .eoi()
    );

    // during reset, acknowledge receipt of read data and write responses,
    // so that a transaction isn't "stuck" the next time the processor wakes up

    assign mem_axi_rready = nreset ? cpu_axi_rready : mem_axi_rvalid;
    assign mem_axi_bready = nreset ? cpu_axi_bready : mem_axi_bvalid;

    // AXI <-> UMI bridge

    axi_umi_bridge #(
        .ARWIDTH(32),
        .RWIDTH(32),
        .AWWIDTH(32),
        .WWIDTH(32)
    ) axi_umi_bridge_i (
        // clock and reset
        .clk(clk),
        .rst(),

        // AXI interface
        .axi_awvalid(mem_axi_awvalid),
        .axi_awready(mem_axi_awready),
        .axi_awaddr(mem_axi_awaddr),
        .axi_wvalid(mem_axi_wvalid),
        .axi_wready(mem_axi_wready),
        .axi_wdata(mem_axi_wdata),
        .axi_wstrb(mem_axi_wstrb),
        .axi_bvalid(mem_axi_bvalid),
        .axi_bready(mem_axi_bready),
        .axi_arvalid(mem_axi_arvalid),
        .axi_arready(mem_axi_arready),
        .axi_araddr(mem_axi_araddr),
        .axi_rvalid(mem_axi_rvalid),
        .axi_rready(mem_axi_rready),
        .axi_rdata(mem_axi_rdata),

        // UMI outbound interface
        .umi_out_packet(umi1_out_packet[255:0]),
        .umi_out_valid(umi1_out_valid[0]),
        .umi_out_ready(umi1_out_ready[0]),

        // UMI inbound interface
        .umi_in_packet(umi1_in_packet[255:0]),
        .umi_in_valid(umi1_in_valid[0]),
        .umi_in_ready(umi1_in_ready[0])
    );

endmodule // ebrick_core

`default_nettype wire
