// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef PCIEDEV_H__
#define PCIEDEV_H__

#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>

#include <sys/mman.h>

#define PCIE_READ_GEN(t, suffix)                                                                   \
    static inline t pcie_read##suffix(void* p) {                                                   \
        uintptr_t i = (uintptr_t)p;                                                                \
        t val;                                                                                     \
                                                                                                   \
        /* Enforce alignment. */                                                                   \
        assert((i % sizeof(val)) == 0);                                                            \
                                                                                                   \
        /* Make access.	*/                                                                         \
        return *(volatile t*)p;                                                                    \
    }

#define PCIE_WRITE_GEN(t, suffix)                                                                  \
    static inline void pcie_write##suffix(void* p, t v) {                                          \
        uintptr_t i = (uintptr_t)p;                                                                \
        t val;                                                                                     \
                                                                                                   \
        /* Enforce alignment. */                                                                   \
        assert((i % sizeof(val)) == 0);                                                            \
                                                                                                   \
        /* Make access.	*/                                                                         \
        *(volatile t*)p = v;                                                                       \
    }                                                                                              \
                                                                                                   \
    static inline void pcie_write##suffix##_strong(void* p, t v) {                                 \
        t dummy;                                                                                   \
        pcie_write##suffix(p, v);                                                                  \
        /* Enforce PCI ordering by reading back the same reg. */                                   \
        dummy = pcie_read##suffix(p);                                                              \
        dummy = dummy;                                                                             \
    }

PCIE_READ_GEN(uint64_t, 64)
PCIE_WRITE_GEN(uint64_t, 64)
PCIE_READ_GEN(uint32_t, 32)
PCIE_WRITE_GEN(uint32_t, 32)
PCIE_READ_GEN(uint16_t, 16)
PCIE_WRITE_GEN(uint16_t, 16)
PCIE_READ_GEN(uint8_t, 8)
PCIE_WRITE_GEN(uint8_t, 8)

static inline void* pcie_bar_map(const char* bdf, int bar_num, uint64_t offset, uint64_t size) {
    char name[] = "/sys/bus/pci/devices/XXXX:XX:XX.X/resourceYY";
    void* p = MAP_FAILED;
    int fd = -1;

    snprintf(name, sizeof name, "/sys/bus/pci/devices/%s/resource%d", bdf, bar_num);

    fd = open(name, O_RDWR | O_SYNC);
    if (fd < 0) {
        goto done;
    }

    p = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, offset);

done:
    if (fd > 0) {
        close(fd);
    }
    return p;
}

static inline void pcie_bar_unmap(void* p, uint64_t size) {
    int r;

    r = munmap(p, size);
    if (r < 0) {
        perror("munmap");
    }
}
#endif
