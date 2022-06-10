// ref: https://github.com/YosysHQ/picorv32/blob/master/testbench.v
// ref: https://github.com/alexforencich/verilog-axi/blob/master/rtl/axil_ram.v

`timescale 1 ns / 1 ps

module axi4_memory #(
	parameter VERBOSE = 0,
	parameter integer MEM_DATA_WIDTH=32,
	parameter integer MEM_ADDR_WIDTH=32,
	parameter integer MEM_CAPACITY=128*1024*8
) (
	/* verilator lint_off MULTIDRIVEN */

	input             clk,
	input             mem_axi_awvalid,
	output reg        mem_axi_awready,
	input [(MEM_ADDR_WIDTH-1):0] mem_axi_awaddr,
	input      [ 2:0] mem_axi_awprot,

	input             mem_axi_wvalid,
	output reg        mem_axi_wready,
	input [(MEM_DATA_WIDTH-1):0] mem_axi_wdata,
	input [((MEM_DATA_WIDTH/8)-1):0] mem_axi_wstrb,

	output reg        mem_axi_bvalid,
	input             mem_axi_bready,

	input             mem_axi_arvalid,
	output reg        mem_axi_arready,
	input [(MEM_ADDR_WIDTH-1):0] mem_axi_araddr,
	input      [ 2:0] mem_axi_arprot,

	output reg        mem_axi_rvalid,
	input             mem_axi_rready,
	output reg [(MEM_DATA_WIDTH-1):0] mem_axi_rdata,

	output reg        should_exit,
	output [15:0]     exit_code
);
	localparam integer MEM_ADDR_SHIFT = $clog2(MEM_ADDR_WIDTH/8);

	reg [(MEM_DATA_WIDTH-1):0] memory [0:((MEM_CAPACITY/MEM_DATA_WIDTH)-1)] /* verilator public */;

	reg verbose;
	initial verbose = ($test$plusargs("verbose") != 0) || VERBOSE;

	initial begin
		mem_axi_awready = 0;
		mem_axi_wready = 0;
		mem_axi_bvalid = 0;
		mem_axi_arready = 0;
		mem_axi_rvalid = 0;
		should_exit = 0;
		exit_code = 0;
	end

	// writes

	integer i;

	always @(posedge clk) begin
		if (mem_axi_awvalid && mem_axi_wvalid &&          // write if address and data are valid
		    ((!mem_axi_awready) && (!mem_axi_wready)) &&  // but don't if the write already happened
			                                              // and we're just handshaking
			((!mem_axi_bvalid) || mem_axi_bready)         // also, stall if past write response
														  // hasn't been acknowledged yet
		) begin
			// perform write
			if (mem_axi_awaddr < MEM_CAPACITY) begin
				for (i=0; i < (MEM_DATA_WIDTH/8); i = i+1) begin
					if (mem_axi_wstrb[i]) begin
						memory[mem_axi_awaddr >> MEM_ADDR_SHIFT][(i*8) +: 8] <= mem_axi_wdata[(i*8) +: 8];
					end
				end
			end else if (mem_axi_awaddr == 'h1000_0008) begin
				if (mem_axi_wdata[15:0] == 16'h3333) begin
					should_exit <= 1;
					exit_code <= mem_axi_wdata[(MEM_DATA_WIDTH-1):16];
				end else if (mem_axi_wdata[15:0] == 16'h5555) begin
					should_exit <= 1;
					exit_code <= 0;
				end
			end else if (mem_axi_awaddr == 'h1000_0000) begin
				$write("%c", mem_axi_wdata[7:0]);
			end else begin
				$display("OUT-OF-BOUNDS MEMORY WRITE TO %08x", mem_axi_awaddr);
				$finish;
			end

			// handshaking
			mem_axi_awready <= 1;
			mem_axi_wready <= 1;
			mem_axi_bvalid <= 1;

			// verbose output
			if (verbose) begin
				$display("WR: ADDR=%0x DATA=%0x STRB=%0b", mem_axi_awaddr, mem_axi_wdata, mem_axi_wstrb);
			end
		end else begin
			mem_axi_awready <= 0;
			mem_axi_wready <= 0;
			mem_axi_bvalid <= mem_axi_bvalid & (~mem_axi_bready);  // keep asserted until acknowledged
		end
	end

	// reads

	always @(posedge clk) begin
		if (mem_axi_arvalid &&                     // perform read if address is valid
		    (!mem_axi_arready) &&                  // but don't if the ready already happened
			                                       // and we're just handshaking
			((!mem_axi_rvalid) || mem_axi_rready)  // also skip if past read data hasn't been
												   // acknowledged yet
		) begin
			if (mem_axi_awaddr < MEM_CAPACITY/8) begin
				mem_axi_rdata <= memory[mem_axi_awaddr >> MEM_ADDR_SHIFT];
			end else if (mem_axi_awaddr == 'h1000_0000) begin
				mem_axi_rdata <= '0;  // non-negative value means "not busy"
			end else begin
				$display("OUT-OF-BOUNDS MEMORY READ FROM %0x", mem_axi_awaddr);
				$finish;
			end

			// handshaking
			mem_axi_arready <= 1;
			mem_axi_rvalid <= 1;

			// verbose output
			if (verbose) begin
				$write("RD: ADDR=%0x DATA=%0x", mem_axi_awaddr, memory[mem_axi_awaddr >> MEM_ADDR_SHIFT]);
				if (mem_axi_arprot[2]) begin
					$display(" INSN");
				end else begin
					$display("");
				end
			end
		end else begin
			mem_axi_arready <= 0;
			mem_axi_rvalid <= mem_axi_rvalid & (~mem_axi_rready);  // assert until acknowledged
		end
	end
endmodule