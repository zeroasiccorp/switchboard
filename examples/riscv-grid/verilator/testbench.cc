#include <cstdio>
#include <iostream>
#include <thread>

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
                if (flag_vcd && (strcmp(flag_vcd, "+vcd")==0)) {
                        Verilated::traceEverOn(true);
                        tfp = new VerilatedVcdC;
                        top->trace (tfp, 99);
                        tfp->open("testbench.vcd");
                }
        #endif

        int yield_every = -1;
        const char* flag_yield = Verilated::commandArgsPlusMatch("yield_every");
        if (flag_yield) {
                std::sscanf(flag_yield, "+yield_every=%d", &yield_every);
        }

        // main loop
        int t=0;
        int yield_count=0;
        top->clk = 0;
        top->eval();
        while (!Verilated::gotFinish()) {
                // update logic
                top->clk ^= 1;
                top->eval();

                // update VCD
                #ifdef USE_VCD
                        if (tfp) {
                                tfp->dump (t);
                        }
                #endif
                t += 5;

                // yield if needed
                if ((yield_every != -1) && top->clk) {
                        if (yield_count >= yield_every) {
                                yield_count = 0;
                                std::this_thread::yield();
                        } else {
                                yield_count++;
                        }
                }
        }

        #ifdef USE_VCD
                if (tfp) {
                        tfp->close();
                }
        #endif

        delete top;
        exit(0);
}