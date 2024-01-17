// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "svdpi.h"

#include <string>

#include <stdio.h>
#include <stdlib.h>

#include "xyce.hpp"

// function definitions
#ifdef __cplusplus
extern "C" {
#endif
extern void pi_sb_xyce_init(char* file);
extern void pi_sb_xyce_put(char* name, double time, double value);
extern void pi_sb_xyce_get(char* name, double time, double* val);
#ifdef __cplusplus
}
#endif

XyceIntf x;

void pi_sb_xyce_init(char* file) {
    x.init(std::string(file));
}

void pi_sb_xyce_put(char* name, double time, double value) {
    x.put(std::string(name), time, value);
}

void pi_sb_xyce_get(char* name, double time, double* value) {
    x.get(std::string(name), time, value);
}
