#include <cstdio>
#include <iostream>
#include <thread>

#include "Vtestbench.h"
#include "verilated.h"

int main(int argc, char **argv, char **env)
{
        Verilated::commandArgs(argc, argv);
        Vtestbench *top = new Vtestbench;

        // main loop
        top->clk = 0;
        top->eval();
        while (!Verilated::gotFinish()) {
                // update logic
                top->clk ^= 1;
                top->eval();
        }

        delete top;
        exit(0);
}
