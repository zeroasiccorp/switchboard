// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <assert.h>
#include <chrono>
#include <memory>
#include <vector>

#include "svdpi.h"
#include "switchboard.hpp"

// function definitions
#ifdef __cplusplus
extern "C" {
#endif
extern void pi_sb_rx_init(int* id, const char* uri, int width);
extern void pi_sb_tx_init(int* id, const char* uri, int width);
extern void pi_sb_recv(int id, svBitVecVal* rdata, svBitVecVal* rdest, svBit* rlast, int* success);
extern void pi_sb_send(int id, const svBitVecVal* sdata, const svBitVecVal* sdest, svBit slast,
    int* success);
extern void pi_time_taken(double* t);
#ifdef __cplusplus
}
#endif

static std::vector<std::unique_ptr<SBRX>> rxconn;
static std::vector<std::unique_ptr<SBTX>> txconn;
static std::vector<int> rxwidth;
static std::vector<int> txwidth;

void pi_sb_rx_init(int* id, const char* uri, int width) {
    rxconn.push_back(std::unique_ptr<SBRX>(new SBRX()));
    rxconn.back()->init(uri);

    // record the width of this connection
    rxwidth.push_back(width);

    // assign the ID of this connection
    *id = rxconn.size() - 1;
}

void pi_sb_tx_init(int* id, const char* uri, int width) {
    txconn.push_back(std::unique_ptr<SBTX>(new SBTX()));
    txconn.back()->init(uri);

    // record the width of this connection
    txwidth.push_back(width);

    // assign the ID of this connection
    *id = txconn.size() - 1;
}

void pi_sb_recv(int id, svBitVecVal* rdata, svBitVecVal* rdest, svBit* rlast, int* success) {
    // make sure this is a valid id
    assert(id < rxconn.size());

    // try to receive an inbound packet
    sb_packet p;
    if (rxconn[id]->recv(p)) {
        memcpy(rdata, p.data, rxwidth[id]);
        *rdest = p.destination;
        *rlast = p.last ? 1 : 0;
        *success = 1;
    } else {
        *success = 0;
    }
}

void pi_sb_send(int id, const svBitVecVal* sdata, const svBitVecVal* sdest, svBit slast,
    int* success) {
    // make sure this is a valid id
    assert(id < txconn.size());

    // form the outbound packet
    sb_packet p;
    memcpy(p.data, sdata, txwidth[id]);
    p.destination = *sdest;
    p.last = slast;

    // try to send the packet
    if (txconn[id]->send(p)) {
        *success = 1;
    } else {
        *success = 0;
    }
}

void pi_time_taken(double* t) {
    static std::chrono::steady_clock::time_point start_time;
    static std::chrono::steady_clock::time_point stop_time;

    // compute time taken in seconds
    stop_time = std::chrono::steady_clock::now();
    *t = 1.0e-6 *
         (std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());
    start_time = std::chrono::steady_clock::now();
}

void pi_start_delay(double value) {
    // WARNING: not tested yet since Icarus Verilog uses VPI and Verilator
    // uses start_delay in main(), not through DPI
    start_delay(value);
}

void pi_max_rate_tick(svBitVecVal* t_us_vec, svBitVecVal* min_period_us_vec) {
    // WARNING: not tested yet since Icarus Verilog uses VPI and Verilator
    // uses max_rate_tick in main(), not through DPI

    // retrieve the previous timestamp and minimum period
    long t_us, min_period_us;
    memcpy(&t_us, t_us_vec, 8);
    memcpy(&min_period_us, min_period_us_vec, 8);

    // call the underlying switchboard function
    max_rate_tick(t_us, min_period_us);

    // store the new timestamp
    memcpy(t_us_vec, &t_us, 8);
}
