// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

// modified from examples/make_tracing_c/sim_main.cpp in https://github.com/verilator/verilator,
// by Wilson Snyder (2017), released as Creative Commons Public Domain

// For Ctrl-C handling
#include <signal.h>

// For std::unique_ptr
#include <memory>

// For changing the clock period
#include <cmath>
#include <iostream>
#include <string>

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

    // parse the clock period, if provided
    double period = 10e-9;
    const char* flag = contextp->commandArgsPlusMatch("period");
    if (flag) {
        std::string full = std::string(flag);
        std::string prefix = "+period=";
        size_t len = prefix.size();
        // match requirements: there must be at least one character after
        // the prefix, and the argument must start with the prefix,
        // ignoring the last character of the prefix, which can be
        // anything (typically "=" or "+")
        if ((full.size() >= (len + 1)) && (full.substr(0, len - 1) == prefix.substr(0, len - 1))) {
            std::string rest = std::string(flag).substr(len);
            period = std::stod(rest);
        }
    }

    // convert the clock period an integer, scaling by the time precision
    uint64_t iperiod = std::round(period * std::pow(10.0, -1.0 * contextp->timeprecision()));
    uint64_t duration0 = iperiod / 2;
    uint64_t duration1 = iperiod - duration0;

    // Set Vtestbench's input signals
    top->clk = 0;
    top->eval();

    // Set up Ctrl-C handler
    signal(SIGINT, sigint_handler);

    // Main loop
    while (!(contextp->gotFinish() || got_sigint)) {
        contextp->timeInc(duration0);
        top->clk = 1;
        top->eval();
        contextp->timeInc(duration1);
        top->clk = 0;
        top->eval();
    }

    // Final model cleanup
    top->final();

    // Return good completion status
    // Don't use exit() or destructor won't get called
    return 0;
}
