#include <iostream>

#include "Vtestbench.h"
#ifdef USE_VCD
        #include "verilated_vcd_c.h"
#else
        #include "verilated.h"
#endif

int main(int argc, char **argv, char **env)
{
        Verilated::commandArgs(argc, argv);
        Vtestbench *top = new Vtestbench;

   	// Tracing (vcd)
        #ifdef USE_VCD
                VerilatedVcdC* tfp = NULL;
                const char* flag_vcd = Verilated::commandArgsPlusMatch("vcd");
                if (flag_vcd && 0==strcmp(flag_vcd, "+vcd")) {
                        Verilated::traceEverOn(true);
                        tfp = new VerilatedVcdC;
                        top->trace (tfp, 99);
                        tfp->open("testbench.vcd");
                }
        #endif

        int t = 0;
        top->clk = 0;
        top->eval();
        while (!Verilated::gotFinish()) {
                top->clk ^= 1;
                top->eval();
                #ifdef USE_VCD
                        if (tfp) {
                                tfp->dump (t);
                        }
                #endif
                t += 5;
        }

        #ifdef USE_VCD
                if (tfp) {
                        tfp->close();
                }
        #endif

        delete top;
        exit(0);
}