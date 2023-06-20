/*
 * C-based subset of umilib.
 */

#ifndef __UMILIB_H__
#define __UMILIB_H__

#include <unistd.h>
#include <assert.h>
#include <string.h>

// ref: umi/rtl/umi_messages.vh
enum UMI_CMD {
    UMI_INVALID         = 0x00,

    // Requests (host -> device)
    UMI_REQ_READ        = 0x01,
    UMI_REQ_WRITE       = 0x03,
    UMI_REQ_POSTED      = 0x05,
    UMI_REQ_RDMA        = 0x07,
    UMI_REQ_ATOMIC      = 0x09,
    UMI_REQ_USER0       = 0x0B,
    UMI_REQ_FUTURE0     = 0x0D,
    UMI_REQ_ERROR       = 0x0F,
    UMI_REQ_LINK        = 0x2F,

    // Response (device -> host)
    UMI_RESP_READ       = 0x02,
    UMI_RESP_WRITE      = 0x04,
    UMI_RESP_USER0      = 0x06,
    UMI_RESP_USER1      = 0x08,
    UMI_RESP_FUTURE0    = 0x0A,
    UMI_RESP_FUTURE1    = 0x0C,
    UMI_RESP_LINK       = 0x0E,

    UMI_REQ_ATOMICADD   = 0x00,
    UMI_REQ_ATOMICAND   = 0x01,
    UMI_REQ_ATOMICOR    = 0x02,
    UMI_REQ_ATOMICXOR   = 0x03,
    UMI_REQ_ATOMICMAX   = 0x04,
    UMI_REQ_ATOMICMIN   = 0x05,
    UMI_REQ_ATOMICMAXU  = 0x06,
    UMI_REQ_ATOMICMINU  = 0x07,
    UMI_REQ_ATOMICSWAP  = 0x08
};

struct umi_packet {
    uint32_t cmd;
    uint64_t dstaddr;
    uint64_t srcaddr;
    uint8_t data[32];
} __attribute__ ((packed));

static inline bool has_umi_resp(uint32_t opcode) {
    return (
        (opcode == UMI_REQ_READ) |
        (opcode == UMI_REQ_WRITE) |
        (opcode == UMI_REQ_ATOMIC)
    );
}

static inline bool has_umi_data(uint32_t opcode) {
    return (
        (opcode == UMI_REQ_WRITE) |
        (opcode == UMI_REQ_POSTED) |
        (opcode == UMI_REQ_RDMA) |
        (opcode == UMI_REQ_ATOMIC) |
        (opcode == UMI_RESP_READ)
    );
}

static inline bool is_umi_req(uint32_t opcode) {
    return (opcode & 0b1) == 0b1;
}

static inline bool is_umi_resp(uint32_t opcode) {
    return (opcode & 0b1) == 0b0;
}

static inline bool is_umi_user(uint32_t opcode) {
    return (
        (opcode == UMI_REQ_USER0) |
        (opcode == UMI_RESP_USER0) |
        (opcode == UMI_RESP_USER1)
    );
}

static inline bool is_umi_future(uint32_t opcode) {
    return (
        (opcode == UMI_REQ_FUTURE0) |
        (opcode == UMI_RESP_FUTURE0) |
        (opcode == UMI_RESP_FUTURE1)
    );
}

static inline uint32_t get_umi_bits(uint32_t cmd, uint32_t offset, uint32_t width) {
    uint32_t mask = (1<<width)-1;
    return ((cmd >> offset) & mask);
}

static inline void set_umi_bits(uint32_t* cmd, uint32_t bits,
    uint32_t offset, uint32_t width) {

    uint32_t mask = (1<<width)-1;

    *cmd = *cmd & (~(mask << offset));
    *cmd = *cmd | (((bits & mask) << offset));
}

static inline uint32_t umi_opcode(uint32_t cmd) {
    return get_umi_bits(cmd, 0, 5);
}

static inline void set_umi_opcode(uint32_t* cmd, uint32_t opcode) {
    set_umi_bits(cmd, opcode, 0, 5);
}

static inline uint32_t umi_size(uint32_t cmd) {
    return get_umi_bits(cmd, 5, 3);
}

static inline void set_umi_size(uint32_t* cmd, uint32_t size) {
    set_umi_bits(cmd, size, 5, 3);
}

static inline uint32_t umi_len(uint32_t cmd) {
    return get_umi_bits(cmd, 8, 8);
}

static inline void set_umi_len(uint32_t* cmd, uint32_t len) {
    set_umi_bits(cmd, len, 8, 8);
}

static inline uint32_t umi_atype(uint32_t cmd) {
    return get_umi_bits(cmd, 8, 8);
}

static inline void set_umi_atype(uint32_t* cmd, uint32_t atype) {
    set_umi_bits(cmd, atype, 8, 8);
}

static inline uint32_t umi_eom(uint32_t cmd) {
    return get_umi_bits(cmd, 22, 1);
}

static inline void set_umi_eom(uint32_t* cmd, uint32_t eom) {
    set_umi_bits(cmd, eom, 22, 1);
}

static inline uint32_t umi_eof(uint32_t cmd) {
    return get_umi_bits(cmd, 23, 1);
}

static inline void set_umi_eof(uint32_t* cmd, uint32_t eof) {
    set_umi_bits(cmd, eof, 23, 1);
}

static inline bool umi_packets_match(umi_packet* a, umi_packet* b) {
    return (memcmp(a, b, 52) == 0);
}

#endif // __UMILIB_H__
