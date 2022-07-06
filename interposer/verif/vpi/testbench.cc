#include <iostream>

#include "Vtestbench_vpi.h"
#include "verilated.h"
int main(int argc, char **argv, char **env)
{
        Verilated::commandArgs(argc, argv);
        Vour *top = new Vtestbench_vpi;
        top->clk = 0;
        top->eval();
        while (!Verilated::gotFinish())
        {
                top->clk ^= 1;
                top->eval();
        }
        delete top;
        exit(0);
}