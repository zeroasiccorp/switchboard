// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "svdpi.h"

#include <memory>
#include <string>
#include <vector>

#include <stdio.h>
#include <stdlib.h>

#include "xyce.hpp"

// function definitions
#ifdef __cplusplus
extern "C" {
#endif
extern void pi_sb_xyce_init(int* id, char* file);
extern void pi_sb_xyce_put(int id, char* name, double time, double value);
extern void pi_sb_xyce_get(int id, char* name, double time, double* val);
#ifdef __cplusplus
}
#endif

static std::vector<std::unique_ptr<XyceIntf>> xyceIntfs;

void pi_sb_xyce_init(int* id, char* file) {
    // add a new Xyce interface
    xyceIntfs.push_back(std::unique_ptr<XyceIntf>(new XyceIntf()));
    xyceIntfs.back()->init(std::string(file));

    // set ID
    *id = xyceIntfs.size() - 1;
}

void pi_sb_xyce_put(int id, char* name, double time, double value) {
    xyceIntfs[id]->put(std::string(name), time, value);
}

void pi_sb_xyce_get(int id, char* name, double time, double* value) {
    xyceIntfs[id]->get(std::string(name), time, value);
}
