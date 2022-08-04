/*******************************************************************************
 * Function:  Universal Memory Interface (UMI) Command Decoder
 * Author:    Andreas Olofsson
 * License:
 *
 * Documentation:
 *
 *
 ******************************************************************************/
module umi_decode
  (
   // Packet Command
   input [31:0]  cmd,
   // Decoded signals
   output 	 cmd_invalid,// invalid transaction
   output 	 cmd_write,// write indicator
   output 	 cmd_read, // read request
   output 	 cmd_atomic,// read-modify-write
    // Controls
   output 	 cmd_write_normal,// write indicator
   output 	 cmd_write_signal,// write with eot signal
   output 	 cmd_write_ack,// write with acknowledge
   output 	 cmd_write_stream,// write stream
   output 	 cmd_write_response,// write response
   output 	 cmd_atomic_swap,
   output 	 cmd_atomic_add,
   output 	 cmd_atomic_and,
   output 	 cmd_atomic_or,
   output 	 cmd_atomic_xor,
   output 	 cmd_atomic_min,
   output 	 cmd_atomic_max,
   //Command Fields
   output [7:0]  cmd_opcode,// raw opcode
   output [3:0]  cmd_size, // burst length(up to 16)
   output [19:0] cmd_user //user field
   );


   // Command grouping
   assign cmd_opcode[7:0] = cmd[7:0];
   assign cmd_size[3:0]   = cmd[11:8];
   assign cmd_user[19:0]  = cmd[31:12];
   assign cmd_read        =  cmd_opcode[3];
   assign cmd_write       = ~cmd_opcode[3];
   assign cmd_atomic      = cmd_opcode[3:0]==4'b1001;
   assign cmd_invalid     = ~|cmd_opcode[7:0];

   // Write controls
   assign cmd_write_signal   = cmd_opcode[2:0]==3'b001;
   assign cmd_write_response = cmd_opcode[2:0]==3'b001;
   assign cmd_write_signal   = cmd_opcode[2:0]==3'b010;
   assign cmd_write_stream   = cmd_opcode[2:0]==3'b011;
   assign cmd_write_ack      = cmd_opcode[2:0]==3'b100;

   // Read transactions
   assign cmd_atomic_swap = cmd_atomic & (cmd_opcode[6:4]==3'b000);
   assign cmd_atomic_add  = cmd_atomic & (cmd_opcode[6:4]==3'b001);
   assign cmd_atomic_and  = cmd_atomic & (cmd_opcode[6:4]==3'b010);
   assign cmd_atomic_or   = cmd_atomic & (cmd_opcode[6:4]==3'b011);
   assign cmd_atomic_xor  = cmd_atomic & (cmd_opcode[6:4]==3'b100);
   assign cmd_atomic_max  = cmd_atomic & (cmd_opcode[6:4]==3'b101);
   assign cmd_atomic_min  = cmd_atomic & (cmd_opcode[6:4]==3'b110);


endmodule // umi_decode
