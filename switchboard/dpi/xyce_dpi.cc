// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "svdpi.h"

#include <stdio.h>
#include <stdlib.h>

#include <N_CIR_XyceCInterface.h>

// function definitions
#ifdef __cplusplus
extern "C" {
#endif
extern void pi_sb_xyce_init(char* file);
extern void pi_sb_xyce_advance(double dt);
extern void pi_sb_xyce_put(char* name, double value);
extern void pi_sb_xyce_get(char* name, double* val);
#ifdef __cplusplus
}
#endif

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

void pi_sb_xyce_init(char* file) {
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
}

void pi_sb_xyce_advance(double dt){
    if (initialized) {
        double actual_time;
        int status = xyce_simulateUntil(xyceObj, sim_time + dt, &actual_time);
        sim_time = actual_time;
    }
}

void pi_sb_xyce_put(char* name, double value) {
    if (initialized) {
        double timeArray [] = {sim_time};
        double voltageArray [] = {value};

        char fullName[100];
        sprintf(fullName, "YDAC!%s", name);

        xyce_updateTimeVoltagePairs(xyceObj, fullName, 1, timeArray, voltageArray);
    }
}

void pi_sb_xyce_get(char* name, double* value) {
    if (initialized) {
        xyce_obtainResponse(xyceObj, name, value);
    }
}
