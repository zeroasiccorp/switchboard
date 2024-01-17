// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <vpi_user.h>

#include <stdio.h>
#include <stdlib.h>

#include <N_CIR_XyceCInterface.h>

bool opened = false;
bool initialized = false;
static void** xyceObj = NULL;

double sim_time = 0.0;

void cleanupFunction() {
    if (opened) {
        xyce_close(xyceObj);
    }

    if (xyceObj) {
        free(xyceObj);
    }
}

PLI_INT32 pi_sb_xyce_init(PLI_BYTE8* userdata) {
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

    // get file
    char* file;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[1], &argval);
        file = argval.value.str;
    }

    // pointer to N_CIR_Xyce object
    xyceObj = (void **) malloc( sizeof(void* [1]) );
    atexit(cleanupFunction);

    // xyce command
    char *argList[] = {
        (char*)("Xyce"),
        (char*)("-quiet"),
        file
    };
    int argc = sizeof(argList)/sizeof(argList[0]);
    char** argv = argList;

    // Open N_CIR_Xyce object
    xyce_open(xyceObj);
    opened = true;

    // Initialize N_CIR_Xyce object
    xyce_initialize(xyceObj, argc, argv);
    initialized = true;

    // Simulate for a small amount of time
    double actual_time;
    xyce_simulateUntil(xyceObj, 1e-10, &actual_time);
    sim_time = actual_time;

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_sb_xyce_advance(PLI_BYTE8* userdata){
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

    // get dt
    double dt;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[1], &argval);
        file = argval.value.real;
    }

    if (initialized) {
        double actual_time;
        int status = xyce_simulateUntil(xyceObj, sim_time + dt, &actual_time);
        sim_time = actual_time;
    }

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
    char* name;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[1], &argval);
        name = argval.value.str;
    }

    // get value
    double value;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[2], &argval);
        value = argval.value.real;
    }

    if (initialized) {
        double timeArray [] = {sim_time};
        double voltageArray [] = {value};

        char fullName[100];
        sprintf(fullName, "YDAC!%s", name);

        xyce_updateTimeVoltagePairs(xyceObj, fullName, 1, timeArray, voltageArray);
    }

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
    char* name;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[1], &argval);
        name = argval.value.str;
    }

    double value;
    if (initialized) {
        xyce_obtainResponse(xyceObj, name, &value);
    }

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
VPI_REGISTER_FUNC(pi_sb_xyce_advance)
VPI_REGISTER_FUNC(pi_sb_xyce_put)
VPI_REGISTER_FUNC(pi_sb_xyce_get)

void (*vlog_startup_routines[])(void) = {
    VPI_REGISTER_FUNC_NAME(pi_sb_xyce_init),
    VPI_REGISTER_FUNC_NAME(pi_sb_xyce_advance),
    VPI_REGISTER_FUNC_NAME(pi_sb_xyce_put),
    VPI_REGISTER_FUNC_NAME(pi_sb_xyce_get),
    0 // last entry must be 0
};
