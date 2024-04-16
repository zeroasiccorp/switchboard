// Linux user-space virt-to-phys mapper

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef PAGEMAP_H_
#define PAGEMAP_H_

#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

/*
 * From https://www.kernel.org/doc/Documentation/admin-guide/mm/pagemap.rst

 * ``/proc/pid/pagemap``.  This file lets a userspace process find out which
   physical frame each virtual page is mapped to.  It contains one 64-bit
   value for each virtual page, containing the following data (from
   ``fs/proc/task_mmu.c``, above pagemap_read):

    * Bits 0-54  page frame number (PFN) if present
    * Bits 0-4   swap type if swapped
    * Bits 5-54  swap offset if swapped
    * Bit  55    pte is soft-dirty (see
      :ref:`Documentation/admin-guide/mm/soft-dirty.rst <soft_dirty>`)
    * Bit  56    page exclusively mapped (since 4.2)
    * Bit  57    pte is uffd-wp write-protected (since 5.13) (see
      :ref:`Documentation/admin-guide/mm/userfaultfd.rst <userfaultfd>`)
    * Bits 58-60 zero
    * Bit  61    page is file-page or shared-anon (since 3.5)
    * Bit  62    page swapped
    * Bit  63    page present
*/

#define PAGEMAP_PFN_MASK ((1ULL << 55) - 1)
#define PAGEMAP_PAGE_PRESENT (1ULL << 63)
#define PAGEMAP_FAILED (~0ULL)

static inline int pagemap_open_self(void) {
    int r;

    r = open("/proc/self/pagemap", O_RDONLY);
    if (r < 0) {
        perror("open");
    }
    return r;
}

// Translate a given virtual ptr into its physical address.
static inline uint64_t pagemap_virt_to_phys(void* ptr) {
    uint64_t va = (uintptr_t)ptr;
    uint64_t pagemap;
    uint64_t offset;
    uint64_t vfn;
    uint64_t pa;
    int pagesize;
    ssize_t r;
    int fd;

    fd = pagemap_open_self();
    if (fd < 0) {
        return PAGEMAP_FAILED;
    }

    pagesize = getpagesize();
    offset = va % pagesize;
    vfn = va / pagesize;
    r = pread(fd, &pagemap, sizeof pagemap, 8 * vfn);
    assert(r == sizeof pagemap);
    close(fd);

    if (!(pagemap & PAGEMAP_PAGE_PRESENT)) {
        return PAGEMAP_FAILED;
    }

    pa = (pagemap & PAGEMAP_PFN_MASK) * pagesize;
    if (!pa) {
        return PAGEMAP_FAILED;
    }

    pa |= offset;
    return pa;
}
#endif
