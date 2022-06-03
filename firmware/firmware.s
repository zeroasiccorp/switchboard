.section .text

.global _start
_start:
        la a0, msg              # a0 = address of msg
        li a1, 0x10000000       # a1 = address of output port

puts:   lbu a2, (a0)            # a2 = load unsigned byte from string
        beqz a2, done           # if byte is null, break the loop

        sw a2, (a1)             # otherwise send byte to output

        addi a0, a0, 1          # increment message pointer and repeat
        j puts

done:   li a0, 0x20000000       # write a magic code to end simulation
        li a1, 123456789
        sw a1, (a0)

        ebreak                  # error out if we get to this point

.section .rodata
msg:
     .string "Hello World!\n"
