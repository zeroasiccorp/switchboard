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

template<typename T>
static inline bool sb_pcie_init(T *s, const char *uri,
                                const char *bdf, int bar_num,
                                char * &map, uint64_t &phys) {
            SB_base *sb_base = s;
            int capacity;
            uint32_t r;

            // Create queue's that fit into a single page.
            capacity = spsc_capacity(getpagesize());
            sb_base->init(uri, capacity);

            // Lock pages into RAM (avoid ondemand allocation or swapping).
            if (sb_base->mlock()) {
                perror("mlock");
                return false;
            }

            phys = pagemap_virt_to_phys(sb_base->get_shm_handle());
            map = (char *) pcie_bar_map(bdf, bar_num, 0, getpagesize());
            if (map == MAP_FAILED) {
                sb_base->deinit();
                return false;
            }

            // TODO Validate the ID and version regs.
            r = pcie_read32(map + REG_ID);
            printf("SB pcie ID=%x\n", r);
            r = pcie_read32(map + REG_CAP);
            printf("SB pcie CAP=%x\n", r);

            pcie_write32(map + REG_QUEUE_ADDRESS_LO, phys);
            pcie_write32(map + REG_QUEUE_ADDRESS_HI, phys >> 32);
            pcie_write32(map + REG_QUEUE_CAPACITY, capacity);
            pcie_write32_strong(map + REG_ACTIVE, 0x1);
            return true;
}

class SBTX_pcie : public SBTX {
    public:
        SBTX_pcie() : m_map(NULL), m_phys(0) { }
        ~SBTX_pcie() {
            pcie_bar_unmap(m_map, getpagesize());
        }

        bool init(const char *uri, const char *bdf, int bar_num = 0) {
            return sb_pcie_init(this, uri, bdf, bar_num, m_map, m_phys);
        }

    private:
        char *m_map;
	uint64_t m_phys;
};

class SBRX_pcie : public SBRX {
    public:
        SBRX_pcie() : m_map(NULL), m_phys(0) { }
        ~SBRX_pcie() {
            pcie_bar_unmap(m_map, getpagesize());
        }

        bool init(const char *uri, const char *bdf, int bar_num = 0) {
            return sb_pcie_init(this, uri, bdf, bar_num, m_map, m_phys);
        }

    private:
        char *m_map;
	uint64_t m_phys;
};

#endif // __SWITCHBOARD_PCIE_HPP__
