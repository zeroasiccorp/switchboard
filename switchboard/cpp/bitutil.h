// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __BITUTIL_H__
#define __BITUTIL_H__

#include <stddef.h>

// highest_bit: determine the index of the most significant non-zero
// bit in a number.

static inline size_t highest_bit(size_t x) {
    size_t retval = 0;
    while ((x >>= 1) != 0) {
        retval++;
    }
    return retval;
}

// lowest_bit: determine index of the least significant non-zero
// bit in a number.

static inline size_t lowest_bit(size_t x) {
    if (x == 0) {
        // if the input is zero, it is convenient to return a value
        // that is larger than the return value for any non-zero
        // input value, which is (sizeof(size_t)*8)-1.
        return sizeof(size_t) * 8;
    } else {
        size_t retval = 0;
        while ((x & 1) == 0) {
            x >>= 1;
            retval++;
        }
        return retval;
    }
}

#endif // #ifndef __BITUTIL_H__
