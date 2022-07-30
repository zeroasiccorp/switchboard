/*******************************************************************************
 * Function:  Universal Memory Interface (UMI) Un-packer
 * Author:    Andreas Olofsson
 * License:
 *
 * Documentation:
 *
 *
 ******************************************************************************/
module umi_unpack
  #(parameter AW = 64,
    parameter PW = 256)
   (
    // Input packet
    input [PW-1:0]    packet_in,
    // Decoded signals
    output 	      cmd_invalid,// invalid transaction
    output 	      cmd_write,// write indicator
    output 	      cmd_read, // read request
    output 	      cmd_atomic,// read-modify-write
    // Controls
    output 	      cmd_write_normal,// write indicator
    output 	      cmd_write_signal,// write with eot signal
    output 	      cmd_write_ack,// write with acknowledge
    output 	      cmd_write_stream,// write stream
    output 	      cmd_write_response,// write response
    output 	      cmd_atomic_swap,
    output 	      cmd_atomic_add,
    output 	      cmd_atomic_and,
    output 	      cmd_atomic_or,
    output 	      cmd_atomic_xor,
    output 	      cmd_atomic_min,
    output 	      cmd_atomic_max,
    //Command Fields
    output [7:0]      cmd_opcode,// raw opcode
    output [3:0]      cmd_size, // burst length(up to 16)
    output [19:0]     cmd_user, //user field
    //Address/Data
    output [AW-1:0]   dstaddr, // read/write target address
    output [AW-1:0]   srcaddr, // read return address
    output [4*AW-1:0] data     // write data
    );

   // command decode
   umi_decode umi_decode(.cmd(packet_in[31:0]),
			 /*AUTOINST*/
			 // Outputs
			 .cmd_invalid		(cmd_invalid),
			 .cmd_write		(cmd_write),
			 .cmd_read		(cmd_read),
			 .cmd_atomic		(cmd_atomic),
			 .cmd_write_normal	(cmd_write_normal),
			 .cmd_write_signal	(cmd_write_signal),
			 .cmd_write_ack		(cmd_write_ack),
			 .cmd_write_stream	(cmd_write_stream),
			 .cmd_write_response	(cmd_write_response),
			 .cmd_atomic_swap	(cmd_atomic_swap),
			 .cmd_atomic_add	(cmd_atomic_add),
			 .cmd_atomic_and	(cmd_atomic_and),
			 .cmd_atomic_or		(cmd_atomic_or),
			 .cmd_atomic_xor	(cmd_atomic_xor),
			 .cmd_atomic_min	(cmd_atomic_min),
			 .cmd_atomic_max	(cmd_atomic_max),
			 .cmd_opcode		(cmd_opcode[7:0]),
			 .cmd_size		(cmd_size[3:0]),
			 .cmd_user		(cmd_user[19:0]));

   // data field unpacker
   generate
      if(AW==64 & PW==256) begin : p256
	 assign dstaddr[31:0]   = packet_in[63:32];
	 assign dstaddr[63:32]  = packet_in[255:224];
	 assign srcaddr[31:0]   = packet_in[95:64];
	 assign srcaddr[63:32]  = packet_in[223:192];
	 assign data[31:0]      = packet_in[127:96];
	 assign data[63:32]     = packet_in[159:128];
	 assign data[95:64]     = packet_in[191:160];
	 assign data[127:96]    = packet_in[223:192];
	 assign data[159:128]   = packet_in[255:224];
	 assign data[191:160]   = packet_in[31:0];
	 assign data[223:192]   = packet_in[63:32];
	 assign data[255:224]   = packet_in[95:64];
      end
   endgenerate

endmodule // umi_unpack
