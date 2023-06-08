#ifndef __UMILIB_HPP__
#define __UMILIB_HPP__

#include <string>
#include "umilib.h"

static inline void umi_pack_burst(umi_packet p, uint8_t data[], int nbytes=32) {
    assert(nbytes <= 32);
    memcpy(&p[3], data, std::min(nbytes, 20));
    if (nbytes > 20) {
        memcpy(p, &data[20], nbytes - 20);
    }
}

static inline void umi_pack(umi_packet p, uint32_t opcode, uint32_t size, uint32_t user,
    uint64_t dstaddr, uint64_t srcaddr, uint8_t data[], int nbytes=16) {

    // form the 32-bit command
    uint32_t cmd_out = 0;
    cmd_out |= (opcode & 0xff);
    cmd_out |= (size & 0xf) << 8;
    cmd_out |= (user & 0xfffff) << 12;

    // populate the packet

    p[7] = (dstaddr >> 32) & 0xffffffff;

    if (is_umi_read_request(opcode) || is_umi_atomic(opcode)) {
        p[6] = (srcaddr >> 32) & 0xffffffff;
    }

    if (nbytes > 0) {
        assert(nbytes <= 16);
        memcpy(&p[3], data, std::min(1<<size, nbytes));
    }

    p[2] = srcaddr & 0xffffffff;
    p[1] = dstaddr & 0xffffffff;
    p[0] = cmd_out;
}

static inline void umi_unpack_burst(const umi_packet p, uint8_t data[], int nbytes=32) {
    assert(nbytes <= 32);

    memcpy(data, &p[3], std::min(nbytes, 20));
    if (nbytes > 20) {
        memcpy(&data[20], p, nbytes - 20);
    }
}

static inline void copy_umi_data(const umi_packet p, uint8_t data[], int nbytes=16) {
    assert(nbytes <= 16);
    memcpy(data, &p[3], nbytes);
}

static inline void umi_unpack(const umi_packet p, uint32_t& opcode, uint32_t& size, uint32_t& user,
    uint64_t& dstaddr, uint64_t& srcaddr, uint8_t data[], int nbytes=16) {

    opcode = umi_opcode(p);
    size = umi_size(p);
    user = umi_user(p);
    dstaddr = umi_dstaddr(p);
    srcaddr = umi_srcaddr(p);
    copy_umi_data(p, data, nbytes);

}

static inline std::string umi_packet_to_str(const umi_packet p) {
    std::string retval = "";

    char buf[128];
    for (int i=7; i>=0; i--) {
        sprintf(buf, "%08x", p[i]);
        retval += buf;
        if (i != 0) {
            retval += "_";
        }
    }

    return retval;
}

static inline std::string umi_opcode_to_str(uint32_t opcode) {
    if (opcode == UMI_INVALID) {
        return "INVALID";
    } else if (is_umi_write_posted(opcode)) {
        return "WRITE-POSTED";
    } else if (is_umi_write_response(opcode)) {
        return "WRITE-RESPONSE";
    } else if (is_umi_write_signal(opcode)) {
        return "WRITE-SIGNAL";
    } else if (is_umi_write_stream(opcode)) {
        return "WRITE-STREAM";
    } else if (is_umi_write_ack(opcode)) {
        return "WRITE-ACK";
    } else if (is_umi_write_multicast(opcode)) {
        return "WRITE-MULTICAST";
    } else if (opcode == UMI_READ_REQUEST) {
        return "READ-REQUEST";
    } else if (opcode == UMI_ATOMIC_ADD) {
        return "ATOMIC-ADD";
    } else if (opcode == UMI_ATOMIC_AND) {
        return "ATOMIC-AND";
    } else if (opcode == UMI_ATOMIC_OR) {
        return "ATOMIC-OR";
    } else if (opcode == UMI_ATOMIC_XOR) {
        return "ATOMIC-XOR";
    } else if (opcode == UMI_ATOMIC_MAX) {
        return "ATOMIC-MAX";
    } else if (opcode == UMI_ATOMIC_MIN) {
        return "ATOMIC-MIN";
    } else if (opcode == UMI_ATOMIC_MAXU) {
        return "ATOMIC-MAXU";
    } else if (opcode == UMI_ATOMIC_MINU) {
        return "ATOMIC-MINU";
    } else if (opcode == UMI_ATOMIC_SWAP) {
        return "ATOMIC-SWAP";
    } else if (is_umi_atomic(opcode)) {
        return "ATOMIC-UNKNOWN";
    } else if (is_umi_reserved(opcode)) {
        return "RESERVED";
    } else {
        return "UNKNOWN";
    }
}

static inline bool str_to_umi_packet(const char* str, umi_packet p) {
    // zero out the packet
    for (int i=0; i<8; i++) {
        p[i] = 0;
    }

    // read in all nibbles into an array
    int shift=28;
    int idxp=7;
    int idxs=0;
    int ncnt=0;
    do {
        // see if this is the end of the string, or the start of a comment
        // (in which case we should ignore the rest of the string)
        char cur = str[idxs++];
        if ((cur == '\0') || (cur == '/')) {
            break;
        } else {
            // parse nibble from character

            uint32_t nibble;
            cur = toupper(cur);

            if (('0' <= cur) && (cur <= '9')) {
                nibble = cur - 48;
            } else if (('A' <= cur) && (cur <= 'F')) {
                nibble = (cur - 65) + 0xA;
            } else {
                // skip character (could be an underscore, whitespace, etc.)
                continue;
            }

            // add nibble to UMI packet
            p[idxp] |= (nibble & 0xf) << shift;

            // update nibble count for validation purposes
            ncnt++;

            // update shift and packet index
            shift -= 4;
            if (shift < 0) {
                shift = 28;
                idxp--;
                if (idxp < 0) {
                    // done reading characters
                    break;
                }
            }
        }
    } while(ncnt < 64);

    // for now, only consider the result valid if all 64 nibbles were read
    // in the future, we might want to allow shorter inputs
    bool valid = (ncnt == 64);
    return valid;
}

static inline bool str_to_umi_packet(std::string str, umi_packet p) {
    return str_to_umi_packet(str.c_str(), p);
}

#endif // __UMILIB_HPP__
