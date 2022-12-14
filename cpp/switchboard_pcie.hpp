/*
 * Switchboard FPGA/PCIe transactor driver.
 */
#ifndef __SWITCHBOARD_PCIE_HPP__
#define __SWITCHBOARD_PCIE_HPP__

#include <string>
#include <array>
#include <cstdio>
#include <thread>
#include <vector>

#include "spsc_queue.h"
#include "switchboard.hpp"
#include "pagemap.h"
#include "pciedev.h"

#define REG_ID			0x00
#define REG_CAP			0x04
#define REG_ACTIVE		0x08
#define REG_QUEUE_ADDRESS_LO	0x0c
#define REG_QUEUE_ADDRESS_HI	0x10
#define REG_QUEUE_CAPACITY	0x14

#define REG_QUEUE_AREA_SIZE	(3 * 4)

class SB_pcie {
    public:
        SB_pcie(int queue_id) : m_queue_id(queue_id), m_map(NULL), m_addr(0) { }

        ~SB_pcie() {
            deinit_host();
        }

        virtual bool init_host(const char *uri, const char *bdf, int bar_num, void *handle) {
            m_addr = pagemap_virt_to_phys(handle);
            m_map = (char *) pcie_bar_map(bdf, bar_num, 0, getpagesize());
            if (m_map == MAP_FAILED) {
                return false;
            }
            return true;
        }

        virtual void deinit_host(void) {
            if (m_map) {
                pcie_bar_unmap(m_map, getpagesize());
            }
        }

        bool init_dev(int capacity) {
            int qoffset = m_queue_id * REG_QUEUE_AREA_SIZE;
            uint32_t r;

            // TODO Validate the ID and version regs.
            r = dev_read32(REG_ID);
            printf("SB pcie ID=%x\n", r);
            r = dev_read32(REG_CAP);
            printf("SB pcie CAP=%x\n", r);

            dev_write32(qoffset + REG_QUEUE_ADDRESS_LO, m_addr);
            dev_write32(qoffset + REG_QUEUE_ADDRESS_HI, m_addr >> 32);
            printf("SB QUEUE_ADDR=%lx\n", m_addr);

            dev_write32(qoffset + REG_QUEUE_CAPACITY, capacity);
            printf("SB CAPACITY=%d\n", capacity);

            dev_write32_strong(REG_ACTIVE, 0x1);
            return true;
        }

        virtual uint32_t dev_read32(uint64_t offset)
        {
                return pcie_read32(m_map + offset);
        }

        virtual void dev_write32(uint64_t offset, uint32_t v)
        {
                pcie_write32(m_map + offset, v);
        }

        virtual void dev_write32_strong(uint64_t offset, uint32_t v)
        {
                pcie_write32_strong(m_map + offset, v);
        }

protected:
        // Queue index.
        int m_queue_id;

	// m_map holds a pointer to a mapped memory area that can be
	// used for register accesses. Not all implementions will use it.
        char *m_map;

	// m_addr holds an address to the SPSC queue's SHM area. For some
	// implementations this will simply be a user-space virtual address
	// and for others it may be a physical address for HW DMA implementations
	// to access.
        uint64_t m_addr;
};


static inline bool sb_init_queue(SB_base *s, const char *uri) {
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

template<typename T>
static inline bool sb_pcie_init(T *s, const char *uri,
                                const char *bdf, int bar_num) {
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
        SBTX_pcie(int queue_id) : SB_pcie(queue_id) {
        }

        ~SBTX_pcie() {
        }

        bool init(const char *uri, const char *bdf, int bar_num) {
            return sb_pcie_init(this, uri, bdf, bar_num);
        }

    private:
};

class SBRX_pcie : public SBRX, public SB_pcie {
    public:
        SBRX_pcie(int queue_id) : SB_pcie(queue_id) {
        }

        ~SBRX_pcie() {
            // pcie unmap
        }

        bool init(const char *uri, const char *bdf, int bar_num) {
            return sb_pcie_init(this, uri, bdf, bar_num);
        }

    private:
};

#endif // __SWITCHBOARD_PCIE_HPP__
