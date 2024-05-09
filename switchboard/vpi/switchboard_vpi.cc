// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <chrono>
#include <memory>
#include <vector>

#include "switchboard.hpp"

#include <vpi_user.h>

static std::vector<std::unique_ptr<SBRX>> rxconn;
static std::vector<std::unique_ptr<SBTX>> txconn;
static std::vector<int> rxwidth;
static std::vector<int> txwidth;
static std::chrono::steady_clock::time_point start_time;

PLI_INT32 pi_sb_rx_init(PLI_BYTE8* userdata) {
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

    // get uri
    std::string uri;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[1], &argval);
        uri = std::string(argval.value.str);
    }

    // initialize the connection
    rxconn.push_back(std::unique_ptr<SBRX>(new SBRX()));
    rxconn.back()->init(uri);

    // get width
    int width;
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        vpi_get_value(argh[2], &argval);
        width = argval.value.integer;
    }

    // remember width
    rxwidth.push_back(width);

    // assign the ID of this connection
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        argval.value.integer = rxconn.size() - 1;
        vpi_put_value(argh[0], &argval, NULL, vpiNoDelay);
    }

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_sb_tx_init(PLI_BYTE8* userdata) {
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

    // get uri
    std::string uri;
    {
        t_vpi_value argval;
        argval.format = vpiStringVal;
        vpi_get_value(argh[1], &argval);
        uri = std::string(argval.value.str);
    }

    // initialize the connection
    txconn.push_back(std::unique_ptr<SBTX>(new SBTX()));
    txconn.back()->init(uri);

    // get width
    int width;
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        vpi_get_value(argh[2], &argval);
        width = argval.value.integer;
    }

    // remember width
    txwidth.push_back(width);

    // assign the ID of this connection
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        argval.value.integer = txconn.size() - 1;
        vpi_put_value(argh[0], &argval, NULL, vpiNoDelay);
    }

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_sb_recv(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get arguments
    vpiHandle args_iter;
    std::vector<vpiHandle> argh;
    {
        vpiHandle systfref;
        systfref = vpi_handle(vpiSysTfCall, NULL);
        args_iter = vpi_iterate(vpiArgument, systfref);
        for (size_t i = 0; i < 5; i++) {
            argh.push_back(vpi_scan(args_iter));
        }
    }

    // get id
    int id;
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        vpi_get_value(argh[0], &argval);
        id = argval.value.integer;
    }

    // read incoming packet

    sb_packet p;
    int success;
    if (rxconn[id]->recv(p)) {
        success = 1;

        t_vpi_value argval;

        // store data
        argval.format = vpiVectorVal;
        s_vpi_vecval vecval[SB_DATA_SIZE / 4];
        argval.value.vector = vecval;

        // determine the number of 32-bit words (rounding up)
        int num_words = (rxwidth[id] + 3) / 4;

        for (int i = 0; i < num_words; i++) {
            argval.value.vector[i].aval = *((uint32_t*)(&p.data[i * 4]));
            argval.value.vector[i].bval = 0;
        }
        vpi_put_value(argh[1], &argval, NULL, vpiNoDelay);

        // store destination
        argval.format = vpiIntVal;
        argval.value.integer = p.destination;
        vpi_put_value(argh[2], &argval, NULL, vpiNoDelay);

        // store last
        argval.format = vpiIntVal;
        argval.value.integer = p.last ? 1 : 0;
        vpi_put_value(argh[3], &argval, NULL, vpiNoDelay);
    } else {
        success = 0;
    }

    // indicate success
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        argval.value.integer = success;
        vpi_put_value(argh[4], &argval, NULL, vpiNoDelay);
    }

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_sb_send(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get arguments
    vpiHandle args_iter;
    std::vector<vpiHandle> argh;
    {
        vpiHandle systfref;
        systfref = vpi_handle(vpiSysTfCall, NULL);
        args_iter = vpi_iterate(vpiArgument, systfref);
        for (size_t i = 0; i < 5; i++) {
            argh.push_back(vpi_scan(args_iter));
        }
    }

    // get id
    int id;
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        vpi_get_value(argh[0], &argval);
        id = argval.value.integer;
    }

    // get outgoing packet
    sb_packet p;
    {
        t_vpi_value argval;

        // store data
        argval.format = vpiVectorVal;
        vpi_get_value(argh[1], &argval);

        // determine the number of 32-bit words (rounding up)
        int num_words = (txwidth[id] + 3) / 4;

        for (int i = 0; i < num_words; i++) {
            *((uint32_t*)(&p.data[i * 4])) = argval.value.vector[i].aval;
        }

        // store destination
        argval.format = vpiIntVal;
        vpi_get_value(argh[2], &argval);
        p.destination = argval.value.integer;

        // store last
        argval.format = vpiIntVal;
        vpi_get_value(argh[3], &argval);
        p.last = argval.value.integer;
    }

    // try to send packet
    int success;
    if (txconn[id]->send(p)) {
        success = 1;
    } else {
        success = 0;
    }

    // indicate success
    {
        t_vpi_value argval;
        argval.format = vpiIntVal;
        argval.value.integer = success;
        vpi_put_value(argh[4], &argval, NULL, vpiNoDelay);
    }

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_time_taken(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get argument

    vpiHandle systfref, args_iter;
    vpiHandle argh;
    t_vpi_value argval;

    systfref = vpi_handle(vpiSysTfCall, NULL);
    args_iter = vpi_iterate(vpiArgument, systfref);
    argh = vpi_scan(args_iter);

    // calculate the time taken
    std::chrono::steady_clock::time_point stop_time = std::chrono::steady_clock::now();
    double t =
        1.0e-6 *
        (std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());
    start_time = stop_time;

    // store the time taken
    argval.format = vpiRealVal;
    argval.value.real = t;
    vpi_put_value(argh, &argval, NULL, vpiNoDelay);

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_start_delay(PLI_BYTE8* userdata) {
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

    // get value
    double value;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[0], &argval);
        value = argval.value.real;
    }

    // call the underlying switchboard function
    start_delay(value);

    // clean up
    vpi_free_object(args_iter);

    // return value unused?
    return 0;
}

PLI_INT32 pi_max_rate_tick(PLI_BYTE8* userdata) {
    (void)userdata; // unused

    // get arguments
    vpiHandle args_iter;
    std::vector<vpiHandle> argh;
    {
        vpiHandle systfref;
        systfref = vpi_handle(vpiSysTfCall, NULL);
        args_iter = vpi_iterate(vpiArgument, systfref);
        for (size_t i = 0; i < 2; i++) {
            argh.push_back(vpi_scan(args_iter));
        }
    }

    // get the timestamp
    long t_us = 0;
    {
        t_vpi_value argval;
        argval.format = vpiVectorVal;
        vpi_get_value(argh[0], &argval);

        t_us |= argval.value.vector[1].aval & 0xffffffff;
        t_us <<= 32;
        t_us |= argval.value.vector[0].aval & 0xffffffff;
    }

    // get max rate
    double max_rate;
    {
        t_vpi_value argval;
        argval.format = vpiRealVal;
        vpi_get_value(argh[1], &argval);
        max_rate = argval.value.real;
    }

    // call the underlying switchboard function
    max_rate_tick(t_us, max_rate);

    // set the timestamp
    {
        t_vpi_value argval;
        argval.format = vpiVectorVal;
        s_vpi_vecval vecval[2]; // two 32-bit words
        argval.value.vector = vecval;

        argval.value.vector[0].aval = t_us & 0xffffffff;
        argval.value.vector[0].bval = 0;

        argval.value.vector[1].aval = (t_us >> 32) & 0xffffffff;
        argval.value.vector[1].bval = 0;

        vpi_put_value(argh[0], &argval, NULL, vpiNoDelay);
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

VPI_REGISTER_FUNC(pi_sb_rx_init)
VPI_REGISTER_FUNC(pi_sb_tx_init)
VPI_REGISTER_FUNC(pi_sb_recv)
VPI_REGISTER_FUNC(pi_sb_send)
VPI_REGISTER_FUNC(pi_time_taken)
VPI_REGISTER_FUNC(pi_start_delay)
VPI_REGISTER_FUNC(pi_max_rate_tick)

void (*vlog_startup_routines[])(void) = {
    VPI_REGISTER_FUNC_NAME(pi_sb_rx_init), VPI_REGISTER_FUNC_NAME(pi_sb_tx_init),
    VPI_REGISTER_FUNC_NAME(pi_sb_recv), VPI_REGISTER_FUNC_NAME(pi_sb_send),
    VPI_REGISTER_FUNC_NAME(pi_time_taken), VPI_REGISTER_FUNC_NAME(pi_start_delay),
    VPI_REGISTER_FUNC_NAME(pi_max_rate_tick),
    0 // last entry must be 0
};
