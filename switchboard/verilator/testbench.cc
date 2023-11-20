// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

// modified from examples/make_tracing_c/sim_main.cpp in https://github.com/verilator/verilator,
// by Wilson Snyder (2017), released as Creative Commons Public Domain

// For Ctrl-C handling
#include <signal.h>

// For std::unique_ptr
#include <memory>

// Include common routines
#include <verilated.h>

// Include model header, generated from Verilating "top.v"
#include "Vtestbench.h"

// Legacy function required only so linking works on Cygwin and MSVC++
double sc_time_stamp() {
    return 0;
}

// ref: https://stackoverflow.com/a/4217052
static volatile int got_sigint = 0;

void sigint_handler(int unused) {
    got_sigint = 1;
}

int main(int argc, char** argv, char** env) {
    // Prevent unused variable warnings
    if (false && argc && argv && env) {}

    // Using unique_ptr is similar to
    // "VerilatedContext* contextp = new VerilatedContext" then deleting at end.
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    // Do not instead make Vtop as a file-scope static variable, as the
    // "C++ static initialization order fiasco" may cause a crash

    // Verilator must compute traced signals
    contextp->traceEverOn(true);

    // Pass arguments so Verilated code can see them, e.g. $value$plusargs
    // This needs to be called before you create any model
    contextp->commandArgs(argc, argv);

    // Construct the Verilated model, from Vtop.h generated from Verilating "top.v".
    // Using unique_ptr is similar to "Vtop* top = new Vtop" then deleting at end.
    // "TOP" will be the hierarchical name of the module.
    const std::unique_ptr<Vtestbench> top{new Vtestbench{contextp.get(), "TOP"}};

    // Set Vtestbench's input signals
    top->clk = 0;
    top->eval();

    // Set up Ctrl-C handler
    signal(SIGINT, sigint_handler);

    // Main loop
    while (!(contextp->gotFinish() || got_sigint)) {
        // Historical note, before Verilator 4.200 Verilated::gotFinish()
        // was used above in place of contextp->gotFinish().
        // Most of the contextp-> calls can use Verilated:: calls instead;
        // the Verilated:: versions just assume there's a single context
        // being used (per thread).  It's faster and clearer to use the
        // newer contextp-> versions.

        contextp->timeInc(1); // 1 timeprecision period passes...
        // Historical note, before Verilator 4.200 a sc_time_stamp()
        // function was required instead of using timeInc.  Once timeInc()
        // is called (with non-zero), the Verilated libraries assume the
        // new API, and sc_time_stamp() will no longer work.

        // Toggle a fast (time/2 period) clock
        top->clk = !top->clk;

        // Evaluate model
        // (If you have multiple models being simulated in the same
        // timestep then instead of eval(), call eval_step() on each, then
        // eval_end_step() on each. See the manual.)
        top->eval();
    }

    // Final model cleanup
    top->final();

    // Return good completion status
    // Don't use exit() or destructor won't get called
    return 0;
}
