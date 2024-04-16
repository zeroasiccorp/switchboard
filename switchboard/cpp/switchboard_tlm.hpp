// Switchboard TLM transactor driver

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __SWITCHBOARD_TLM_HPP__
#define __SWITCHBOARD_TLM_HPP__

#include <array>
#include <cstdio>
#include <string>
#include <thread>
#include <vector>

#include "spsc_queue.h"
#include "switchboard.hpp"
#include "switchboard_pcie.hpp"

#define SC_INCLUDE_DYNAMIC_PROCESSES

#include "systemc"
using namespace sc_core;
using namespace sc_dt;
using namespace std;

#include "tlm.h"
#include "tlm_utils/simple_initiator_socket.h"
#include "tlm_utils/simple_target_socket.h"

class SB_tlm : public SB_pcie {
  public:
    tlm_utils::simple_initiator_socket<SB_tlm> socket;

    SB_tlm(int queue_id) : SB_pcie(queue_id) {}

    bool init_host(const char* uri, const char* bdf, int bar_num, void* handle) {
        assert(handle);
        m_addr = (uintptr_t)handle;
        return true;
    }

    void dev_access(tlm::tlm_command cmd, uint64_t offset, void* buf, unsigned int len) {
        unsigned char* buf8 = (unsigned char*)buf;
        sc_time delay = SC_ZERO_TIME;
        tlm::tlm_generic_payload tr;

        tr.set_command(cmd);
        tr.set_address(offset);
        tr.set_data_ptr(buf8);
        tr.set_data_length(len);
        tr.set_streaming_width(len);
        tr.set_dmi_allowed(false);
        tr.set_response_status(tlm::TLM_INCOMPLETE_RESPONSE);

        socket->b_transport(tr, delay);
        assert(tr.get_response_status() == tlm::TLM_OK_RESPONSE);
    }

    uint32_t dev_read32(uint64_t offset) {
        uint32_t r;
        assert((offset & 3) == 0);
        dev_access(tlm::TLM_READ_COMMAND, offset, &r, sizeof(r));
        return r;
    }

    void dev_write32(uint64_t offset, uint32_t v) {
        assert((offset & 3) == 0);
        dev_access(tlm::TLM_WRITE_COMMAND, offset, &v, sizeof(v));
    }

    void dev_write32_strong(uint64_t offset, uint32_t v) {
        uint32_t dummy;

        dev_write32(offset, v);
        // Enforce PCIe ordering.
        dummy = dev_read32(offset);
        dummy = dummy;
    }
};

class SBTX_tlm : public SBTX, public SB_tlm {
  public:
    SBTX_tlm(int queue_id) : SB_tlm(queue_id) {}

    bool init(const char* uri) {
        return sb_pcie_init(this, uri, NULL, -1);
    }
};

class SBRX_tlm : public SBRX, public SB_tlm {
  public:
    SBRX_tlm(int queue_id) : SB_tlm(queue_id) {}

    bool init(const char* uri) {
        return sb_pcie_init(this, uri, NULL, -1);
    }
};
#endif
