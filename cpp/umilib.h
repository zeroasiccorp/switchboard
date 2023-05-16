/*
 * C-based subset of umilib.
 */

#ifndef __UMILIB_H__
#define __UMILIB_H__

#include <unistd.h>
#include <assert.h>

// ref: umi/rtl/umi_messages.vh
enum UMI_CMD {
    UMI_INVALID         = 0x00,
    UMI_WRITE_POSTED    = 0x01,
    UMI_WRITE_RESPONSE  = 0x03,
    UMI_WRITE_SIGNAL    = 0x05,
    UMI_WRITE_STREAM    = 0x07,
    UMI_WRITE_ACK       = 0x09,
    UMI_WRITE_MULTICAST = 0x0B,
    UMI_READ_REQUEST    = 0x02,
    UMI_ATOMIC_ADD      = 0x04,
    UMI_ATOMIC_AND      = 0x14,
    UMI_ATOMIC_OR       = 0x24,
    UMI_ATOMIC_XOR      = 0x34,
    UMI_ATOMIC_MAX      = 0x44,
    UMI_ATOMIC_MIN      = 0x54,
    UMI_ATOMIC_MAXU     = 0x64,
    UMI_ATOMIC_MINU     = 0x74,
    UMI_ATOMIC_SWAP     = 0x84,
    UMI_ATOMIC          = 0x04
};

typedef uint32_t umi_packet[8];

static inline bool is_umi_invalid(uint32_t opcode) {
    return (opcode == UMI_INVALID);
}

static inline bool is_umi_read_request(uint32_t opcode) {
    return (opcode == UMI_READ_REQUEST);
}

static inline bool is_umi_write_posted(uint32_t opcode) {
    return (opcode & 0b00001111) == UMI_WRITE_POSTED;
}

static inline bool is_umi_write_response(uint32_t opcode) {
    return (opcode & 0b00001111) == UMI_WRITE_RESPONSE;
}

static inline bool is_umi_write_signal(uint32_t opcode) {
    return (opcode & 0b00001111) == UMI_WRITE_SIGNAL;
}

static inline bool is_umi_write_stream(uint32_t opcode) {
    return (opcode & 0b00001111) == UMI_WRITE_STREAM;
}

static inline bool is_umi_write_ack(uint32_t opcode) {
    return (opcode & 0b00001111) == UMI_WRITE_ACK;
}

static inline bool is_umi_write_multicast(uint32_t opcode) {
    return (opcode & 0b00001111) == UMI_WRITE_MULTICAST;
}

static inline bool is_umi_write(uint32_t opcode) {
    return ((opcode & 0b1) == 0b1) && ((opcode >> 1) & 0b111) <= 5;
}

static inline bool is_umi_atomic(uint32_t opcode) {
    return ((opcode & 0xf) == UMI_ATOMIC);
}

static inline bool is_umi_reserved(uint32_t opcode) {
    return (
        ((opcode & 0b1111) == 0b1101) |
        ((opcode & 0b1111) == 0b1111) |
        ((opcode & 0b1111) == 0b0110) |
        ((opcode & 0b1111) == 0b1000) |
        ((opcode & 0b1111) == 0b1010) |
        ((opcode & 0b1111) == 0b1100) |
        ((opcode & 0b1111) == 0b1110)
    );
}

static inline uint32_t umi_opcode(const umi_packet p) {
    return (p[0] & 0xff);
}

static inline uint32_t umi_size(const umi_packet p) {
    return (p[0] >> 8) & 0xf;
}

static inline uint32_t umi_user(const umi_packet p) {
    return (p[0] >> 12) & 0xfffff;
}

static inline uint64_t umi_dstaddr(const umi_packet p) {
    uint64_t retval;

    retval = 0;
    retval |= p[7];
    retval <<= 32;
    retval |= p[1];

    return retval;
}

static inline uint64_t umi_srcaddr(const umi_packet p) {
    uint64_t retval;

    retval = 0;
    retval |= p[6];
    retval <<= 32;
    retval |= p[2];

    return retval;
}

static inline bool umi_packets_match(umi_packet a, umi_packet b) {
    return (memcmp(a, b, 32) == 0);
}

#endif // __UMILIB_H__
