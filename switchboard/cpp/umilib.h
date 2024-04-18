// C-based subset of umilib

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __UMILIB_H__
#define __UMILIB_H__

#include <assert.h>
#include <string.h>
#include <unistd.h>

// ref: umi/rtl/umi_messages.vh
enum UMI_CMD {
    UMI_INVALID = 0x00,

    // Requests (host -> device)
    UMI_REQ_READ = 0x01,
    UMI_REQ_WRITE = 0x03,
    UMI_REQ_POSTED = 0x05,
    UMI_REQ_RDMA = 0x07,
    UMI_REQ_ATOMIC = 0x09,
    UMI_REQ_USER0 = 0x0B,
    UMI_REQ_FUTURE0 = 0x0D,
    UMI_REQ_ERROR = 0x0F,
    UMI_REQ_LINK = 0x2F,

    // Response (device -> host)
    UMI_RESP_READ = 0x02,
    UMI_RESP_WRITE = 0x04,
    UMI_RESP_USER0 = 0x06,
    UMI_RESP_USER1 = 0x08,
    UMI_RESP_FUTURE0 = 0x0A,
    UMI_RESP_FUTURE1 = 0x0C,
    UMI_RESP_LINK = 0x0E
};

enum UMI_ATOMIC {
    UMI_REQ_ATOMICADD = 0x00,
    UMI_REQ_ATOMICAND = 0x01,
    UMI_REQ_ATOMICOR = 0x02,
    UMI_REQ_ATOMICXOR = 0x03,
    UMI_REQ_ATOMICMAX = 0x04,
    UMI_REQ_ATOMICMIN = 0x05,
    UMI_REQ_ATOMICMAXU = 0x06,
    UMI_REQ_ATOMICMINU = 0x07,
    UMI_REQ_ATOMICSWAP = 0x08
};

// TODO: make this flexible
#define UMI_PACKET_DATA_BYTES 32

typedef struct umi_packet {
    uint32_t cmd;
    uint64_t dstaddr;
    uint64_t srcaddr;
    uint8_t data[UMI_PACKET_DATA_BYTES];
} __attribute__((packed)) umi_packet;

static inline bool has_umi_resp(uint32_t opcode) {
    return ((opcode == UMI_REQ_READ) || (opcode == UMI_REQ_WRITE) || (opcode == UMI_REQ_ATOMIC));
}

static inline bool has_umi_data(uint32_t opcode) {
    return ((opcode == UMI_REQ_WRITE) || (opcode == UMI_REQ_POSTED) || (opcode == UMI_REQ_ATOMIC) ||
            (opcode == UMI_REQ_USER0) || (opcode == UMI_REQ_FUTURE0) || (opcode == UMI_RESP_READ) ||
            (opcode == UMI_RESP_USER1) || (opcode == UMI_RESP_FUTURE1));
}

static inline bool allows_umi_merge(uint32_t opcode) {
    return ((opcode == UMI_REQ_READ) || (opcode == UMI_REQ_WRITE) || (opcode == UMI_REQ_POSTED) ||
            (opcode == UMI_REQ_RDMA) || (opcode == UMI_RESP_READ) || (opcode == UMI_RESP_WRITE));
}

static inline bool is_umi_invalid(uint32_t opcode) {
    return opcode == 0;
}

static inline bool is_umi_req(uint32_t opcode) {
    return (opcode & 0b1) == 0b1;
}

static inline bool is_umi_resp(uint32_t opcode) {
    return (opcode != 0) && ((opcode & 0b1) == 0b0);
}

static inline bool is_umi_user(uint32_t opcode) {
    return ((opcode == UMI_REQ_USER0) | (opcode == UMI_RESP_USER0) | (opcode == UMI_RESP_USER1));
}

static inline bool is_umi_future(uint32_t opcode) {
    return (
        (opcode == UMI_REQ_FUTURE0) | (opcode == UMI_RESP_FUTURE0) | (opcode == UMI_RESP_FUTURE1));
}

static inline uint32_t get_umi_bits(uint32_t cmd, uint32_t offset, uint32_t width) {
    uint32_t mask = (1 << width) - 1;
    return ((cmd >> offset) & mask);
}

static inline void set_umi_bits(uint32_t* cmd, uint32_t bits, uint32_t offset, uint32_t width) {

    uint32_t mask = (1 << width) - 1;

    *cmd = *cmd & (~(mask << offset));
    *cmd = *cmd | (((bits & mask) << offset));
}

#define DECL_UMI_GETTER(FIELD, OFFSET, WIDTH)                                                      \
    static inline uint32_t umi_##FIELD(uint32_t cmd) {                                             \
        return get_umi_bits(cmd, OFFSET, WIDTH);                                                   \
    }

#define DECL_UMI_SETTER(FIELD, OFFSET, WIDTH)                                                      \
    static inline void set_umi_##FIELD(uint32_t* cmd, uint32_t FIELD) {                            \
        set_umi_bits(cmd, FIELD, OFFSET, WIDTH);                                                   \
    }

#define DECL_UMI_FIELD(FIELD, OFFSET, WIDTH)                                                       \
    DECL_UMI_GETTER(FIELD, OFFSET, WIDTH)                                                          \
    DECL_UMI_SETTER(FIELD, OFFSET, WIDTH)

DECL_UMI_FIELD(opcode, 0, 5)
DECL_UMI_FIELD(size, 5, 3)
static inline uint32_t umi_len(uint32_t cmd) {
    if (umi_opcode(cmd) == UMI_REQ_ATOMIC) {
        return 0;
    } else {
        return get_umi_bits(cmd, 8, 8);
    }
}
DECL_UMI_SETTER(len, 8, 8)
DECL_UMI_FIELD(atype, 8, 8)
DECL_UMI_FIELD(qos, 16, 4)
DECL_UMI_FIELD(prot, 20, 2)
DECL_UMI_FIELD(eom, 22, 1)
DECL_UMI_FIELD(eof, 23, 1)
DECL_UMI_FIELD(ex, 24, 1)

static inline bool umi_packets_match(umi_packet* a, umi_packet* b) {
    return (memcmp(a, b, 52) == 0);
}

#endif // __UMILIB_H__
