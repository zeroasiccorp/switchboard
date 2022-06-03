// Copyright lowRISC contributors.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

#include <cassert>
#include <fstream>
#include <iostream>

#include "Vibex_simple_system__Syms.h"
#include "ibex_pcounts.h"
#include "verilated_toplevel.h"
#include "verilator_memutil.h"
#include "verilator_sim_ctrl.h"

int main(int argc, char **argv) {
    // initialize simulation    
    ibex_simple_system _top;
    VerilatorSimCtrl &simctrl = VerilatorSimCtrl::GetInstance();
    simctrl.SetTop(&_top, &_top.IO_CLK, &_top.IO_RST_N,
                   VerilatorSimCtrlFlags::ResetPolarityNegative);

    // set up memory
    VerilatorMemUtil _memutil;
    MemArea _ram("TOP.ibex_simple_system.u_ram.u_ram.gen_generic.u_impl_generic", 1024 * 1024, 4);
    _memutil.RegisterMemoryArea("ram", 0x0, &_ram);
    simctrl.RegisterExtension(&_memutil);

    // parse command-line arguments
    bool exit_app = false;
    int ret_code = simctrl.ParseCommandArgs(argc, argv, exit_app);
    if (exit_app) {
        return ret_code;
    }

    // run simulation
    simctrl.RunSimulation();
    if (!simctrl.WasSimulationSuccessful()) {
        return 1;
    }
    
    // exit program
    return 0;
}
