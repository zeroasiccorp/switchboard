.section .text

.global _start
_start: la a0, msg              # a0 = address of msg
        li a1, 0x10000000       # a1 = address of output port

puts:   lbu a2, (a0)            # a2 = load unsigned byte from string
        beqz a2, done           # if byte is null, break the loop

uwait:  lw a3, (a1)             # wait for UART to be ready
        bltz a3, uwait

        sw a2, (a1)             # send byte to output

        addi a0, a0, 1          # increment message pointer and repeat
        j puts

done:   li a0, 0x100000         # shut down the machine
        li a1, 0x5555
        sw a1, (a0)

        ebreak

.section .rodata
msg:
     .string "Hello World!\n"
