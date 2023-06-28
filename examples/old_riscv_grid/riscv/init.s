# ref: https://wiki.osdev.org/RISC-V_Bare_Bones

.section .text.init

.global _start
_start:
# set the stack pointer
    la sp, __stack_top

# call the main function
    call main          

# loop forever if we get here
end:
    j end
