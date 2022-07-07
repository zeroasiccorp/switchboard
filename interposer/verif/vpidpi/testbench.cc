#include <iostream>

#include "Vtestbench.h"
#include "verilated.h"
int main(int argc, char **argv, char **env)
{
        Verilated::commandArgs(argc, argv);
        Vtestbench *top = new Vtestbench;
        top->clk = 0;
        top->eval();
        while (!Verilated::gotFinish()) {
                top->clk ^= 1;
                top->eval();
        }
        delete top;
        exit(0);
}