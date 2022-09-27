/*******************************************************************************
 * Function:  Universal Memory Interface (UMI) Packer
 * Author:    Andreas Olofsson
 * License:
 *
 * Documentation:
 *
 *
 ******************************************************************************/
module umi_pack
  #(parameter AW = 64,
    parameter PW = 256)
   (
    // Command inputs
    input [7:0]      opcode,
    input [3:0]      size,// number of bytes to transfer
    input [19:0]     user, // user control field
    input 	     burst, // active burst in process
    // Address/Data
    input [AW-1:0]   dstaddr, // destination address
    input [AW-1:0]   srcaddr, // source address (for reads/atomics)
    input [4*AW-1:0] data, // data
    // Output packet
    output [PW-1:0]  packet_out
    );

   wire [31:0] 	     cmd_out;
   wire [255:0]      data_out;

   // dommand packer
   assign cmd_out[7:0]   = opcode[7:0];
   assign cmd_out[11:8]  = size[3:0];
   assign cmd_out[31:12] = user[19:0];

   // data/address packer
   wire cmd_read;
   generate
      if(AW==64 & PW==256) begin : p256
	 // see README to understand why...
	 assign data_out[255:0] = {data[159:0], data[255:160]};
	 // driving data baseed on transaction type
	 assign packet_out[31:0]    = burst ? data_out[31:0]  : cmd_out[31:0];
	 assign packet_out[63:32]   = burst ? data_out[63:32] : dstaddr[31:0];
	 assign packet_out[95:64]   = burst ? data_out[95:64] : srcaddr[31:0];
	 assign packet_out[191:96]  = data_out[191:96];
	 assign packet_out[223:192] = cmd_read ? srcaddr[63:32] : data_out[223:192];
	 assign packet_out[255:224] = burst ? data_out[255:224] : dstaddr[63:32];
      end
   endgenerate

   // decoding signals needed for packet mux
   umi_decode umi_decode (// input
			  .cmd      (cmd_out[31:0]),
			  // output
			  .cmd_read (cmd_read));

endmodule // umi_pack
