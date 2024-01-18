// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <vpi_user.h>

#include <string>

#include <stdio.h>
#include <stdlib.h>

#include "xyce.hpp"

XyceIntf x;

PLI_INT32 pi_sb_xyce_init(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get arguments
    vpiHandle args_iter;
    std::vector<vpiHandle> argh;
    {
        vpiHandle systfref;
        systfref = vpi_handle(vpiSysTfCall, NULL);
        args_iter = vpi_iterate(vpiArgument, systfref);
        for (size_t i = 0; i < 1; i++) {
            argh.push_back(vpi_scan(args_iter));
        }
    }

    // get file
    std::string file;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[0], &argval);
        file = std::string(argval.value.str);
    }

    x.init(file);

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_sb_xyce_put(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get arguments
    vpiHandle args_iter;
    std::vector<vpiHandle> argh;
    {
        vpiHandle systfref;
        systfref = vpi_handle(vpiSysTfCall, NULL);
        args_iter = vpi_iterate(vpiArgument, systfref);
        for (size_t i = 0; i < 3; i++) {
            argh.push_back(vpi_scan(args_iter));
        }
    }

    // get name
    std::string name;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[0], &argval);
        name = std::string(argval.value.str);
    }

    // get time
    double time;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[1], &argval);
        time = argval.value.real;
    }

    // get value
    double value;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[2], &argval);
        value = argval.value.real;
    }

    x.put(name, time, value);

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_sb_xyce_get(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get arguments
    vpiHandle args_iter;
    std::vector<vpiHandle> argh;
    {
        vpiHandle systfref;
        systfref = vpi_handle(vpiSysTfCall, NULL);
        args_iter = vpi_iterate(vpiArgument, systfref);
        for (size_t i = 0; i < 3; i++) {
            argh.push_back(vpi_scan(args_iter));
        }
    }

    // get name
    std::string name;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[0], &argval);
        name = std::string(argval.value.str);
    }

    // get time
    double time;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[1], &argval);
        time = argval.value.real;
    }

    // get value
    double value;
    x.get(name, time, &value);

    // put value
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        argval.value.real = value;
        vpi_put_value(argh[2], &argval, NULL, vpiNoDelay);
    }

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

// macro that creates a function to register PLI functions

#define VPI_REGISTER_FUNC_NAME(name) register_##name
#define VPI_REGISTER_FUNC(name)                                                                    \
    void VPI_REGISTER_FUNC_NAME(name)(void) {                                                      \
        s_vpi_systf_data data = {vpiSysTask, 0, (char*)("$" #name), name, 0, 0, 0};                \
                                                                                                   \
        vpi_register_systf(&data);                                                                 \
    }

// create the PLI registration functions using this macro

VPI_REGISTER_FUNC(pi_sb_xyce_init)
VPI_REGISTER_FUNC(pi_sb_xyce_put)
VPI_REGISTER_FUNC(pi_sb_xyce_get)

void (*vlog_startup_routines[])(void) = {
    VPI_REGISTER_FUNC_NAME(pi_sb_xyce_init), VPI_REGISTER_FUNC_NAME(pi_sb_xyce_put),
    VPI_REGISTER_FUNC_NAME(pi_sb_xyce_get),
    0 // last entry must be 0
};
