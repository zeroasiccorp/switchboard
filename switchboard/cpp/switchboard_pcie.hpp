// Switchboard FPGA/PCIe transactor driver

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __SWITCHBOARD_PCIE_HPP__
#define __SWITCHBOARD_PCIE_HPP__

#include <array>
#include <cstdio>
#include <string>
#include <thread>
#include <vector>

#include "pagemap.h"
#include "pciedev.h"
#include "spsc_queue.h"
#include "switchboard.hpp"

#undef D
#define D(x)

#define REG_ID 0x000
#define REG_ID_FPGA 0x1234

#define REG_CAP 0x004

#define REG_ENABLE 0x100
#define REG_RESET 0x104
#define REG_STATUS 0x108
#define REG_QUEUE_ADDRESS_LO 0x10c
#define REG_QUEUE_ADDRESS_HI 0x110
#define REG_QUEUE_CAPACITY 0x114

#define REG_QUEUE_ADDR_SIZE 0x100 // size of addr space dedicated to each queue

// Map enough space to configure 256 queues + global config.
#define PCIE_BAR_MAP_SIZE (REG_QUEUE_ADDR_SIZE * 256 + REG_ENABLE)

// Max nr of retries when resetting or disabling queue's.
#define MAX_RETRY 3

template <typename T> static inline void sb_pcie_deinit(T* s) {

    // Needs to be done in reverse order.
    s->deinit_dev();
    s->deinit_host();
}

class SB_pcie {
  public:
    SB_pcie(int queue_id) : m_queue_id(queue_id), m_map(NULL), m_addr(0) {}

    ~SB_pcie() {
        sb_pcie_deinit(this);
    }

    virtual bool init_host(const char* uri, const char* bdf, int bar_num, void* handle) {
        m_addr = pagemap_virt_to_phys(handle);
        m_map = (char*)pcie_bar_map(bdf, bar_num, 0, PCIE_BAR_MAP_SIZE);
        if (m_map == MAP_FAILED) {
            m_map = NULL;
            return false;
        }
        return true;
    }

    virtual void deinit_host(void) {
        if (m_map) {
            pcie_bar_unmap(m_map, PCIE_BAR_MAP_SIZE);
            m_map = NULL;
        }
    }

    bool init_dev(int capacity) {
        int qoffset = m_queue_id * REG_QUEUE_ADDR_SIZE;
        int reset_retry = 0;
        uint32_t r;

        r = dev_read32(REG_ID);
        D(printf("SB pcie ID=%x\n", r));
        if (r >> 16 != REG_ID_FPGA) {
            printf("%s: Incompatible REG_ID=%x\n", __func__, r);
            return false;
        }

        r = dev_read32(REG_CAP);
        D(printf("SB pcie CAP=%x\n", r));

        // Reset the device.
        dev_write32(qoffset + REG_RESET, 0x1);
        D(printf("Read reset state\n"));
        while (dev_read32(qoffset + REG_STATUS) != 0x1) {
            if (reset_retry++ >= MAX_RETRY) {
                return false;
            }
            usleep(100 * 1000);
        }

        dev_write32(qoffset + REG_QUEUE_ADDRESS_LO, m_addr);
        dev_write32(qoffset + REG_QUEUE_ADDRESS_HI, m_addr >> 32);
        D(printf("SB QUEUE_ADDR=%lx\n", m_addr));

        dev_write32(qoffset + REG_QUEUE_CAPACITY, capacity);
        D(printf("SB CAPACITY=%d\n", capacity));

        dev_write32_strong(qoffset + REG_ENABLE, 0x1);
        return true;
    }

    void deinit_dev() {
        int disable_retry = 0;

        if (!m_map) {
            return;
        }
        int qoffset = m_queue_id * REG_QUEUE_ADDR_SIZE;

        // Must disable queue and wait for it to quiesce before unmapping
        // queue shared memory, otherwise FPGA may read from/write to memory
        // that gets reallocated to another process.
        dev_write32_strong(qoffset + REG_ENABLE, 0x0);
        while (dev_read32(qoffset + REG_STATUS) != 0x1) {
            if (disable_retry++ >= MAX_RETRY) {
                return;
            }
            usleep(100 * 1000);
        }
    }

    virtual uint32_t dev_read32(uint64_t offset) {
        assert(m_map);
        assert(offset <= PCIE_BAR_MAP_SIZE - 4);
        return pcie_read32(m_map + offset);
    }

    virtual void dev_write32(uint64_t offset, uint32_t v) {
        assert(m_map);
        assert(offset <= PCIE_BAR_MAP_SIZE - 4);
        pcie_write32(m_map + offset, v);
    }

    virtual void dev_write32_strong(uint64_t offset, uint32_t v) {
        assert(m_map);
        assert(offset <= PCIE_BAR_MAP_SIZE - 4);
        pcie_write32_strong(m_map + offset, v);
    }

  protected:
    // Queue index.
    int m_queue_id;

    // m_map holds a pointer to a mapped memory area that can be
    // used for register accesses. Not all implementations will use it.
    char* m_map;

    // m_addr holds an address to the SPSC queue's SHM area. For some
    // implementations this will simply be a user-space virtual address
    // and for others it may be a physical address for HW DMA implementations
    // to access.
    uint64_t m_addr;
};

static inline bool sb_init_queue(SB_base* s, const char* uri) {
    int capacity;

    // Create queue's that fit into a single page.
    capacity = spsc_capacity(getpagesize());
    s->init(uri, capacity);

    // Lock pages into RAM (avoid ondemand allocation or swapping).
    if (s->mlock()) {
        perror("mlock");
        s->deinit();
        return false;
    }
    return true;
}

template <typename T>
static inline bool sb_pcie_init(T* s, const char* uri, const char* bdf, int bar_num) {
    sb_init_queue(s, uri);

    if (!s->init_host(uri, bdf, bar_num, s->get_shm_handle())) {
        s->deinit();
        return false;
    }

    if (!s->init_dev(s->get_capacity())) {
        s->deinit();
        return false;
    }
    return true;
}

class SBTX_pcie : public SBTX, public SB_pcie {
  public:
    SBTX_pcie(int queue_id) : SB_pcie(queue_id) {}

    bool init(std::string uri, std::string bdf, int bar_num) {
        return init(uri.c_str(), bdf.c_str(), bar_num);
    }

    bool init(const char* uri, const char* bdf, int bar_num) {
        return sb_pcie_init(this, uri, bdf, bar_num);
    }

    void deinit(void) {
        sb_pcie_deinit(this);
    }

  private:
};

class SBRX_pcie : public SBRX, public SB_pcie {
  public:
    SBRX_pcie(int queue_id) : SB_pcie(queue_id) {}

    bool init(std::string uri, std::string bdf, int bar_num) {
        return init(uri.c_str(), bdf.c_str(), bar_num);
    }

    bool init(const char* uri, const char* bdf, int bar_num) {
        return sb_pcie_init(this, uri, bdf, bar_num);
    }

    void deinit(void) {
        sb_pcie_deinit(this);
    }

  private:
};

#endif // __SWITCHBOARD_PCIE_HPP__
