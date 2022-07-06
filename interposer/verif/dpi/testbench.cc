#include <iostream>

#include "Vtestbench_dpi.h"
#include "verilated.h"
int main(int argc, char **argv, char **env)
{
        Verilated::commandArgs(argc, argv);
        Vtestbench_dpi *top = new Vtestbench_dpi;
        top->clk = 0;
        top->eval();
        while (!Verilated::gotFinish()) {
                top->clk ^= 1;
                top->eval();
        }
        delete top;
        exit(0);
}