// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __UMILIB_HPP__
#define __UMILIB_HPP__

#include "umilib.h"
#include <string>

static inline uint32_t umi_pack(uint32_t opcode, uint32_t atype, uint32_t size, uint32_t len,
    uint32_t eom, uint32_t eof, uint32_t qos = 0, uint32_t prot = 0, uint32_t ex = 0) {

    uint32_t cmd = 0;

    set_umi_opcode(&cmd, opcode);
    set_umi_size(&cmd, size);
    if (opcode != UMI_REQ_ATOMIC) {
        set_umi_len(&cmd, len);
    } else {
        set_umi_atype(&cmd, atype);
    }
    set_umi_qos(&cmd, qos);
    set_umi_prot(&cmd, prot);
    set_umi_eom(&cmd, eom);
    set_umi_eof(&cmd, eof);
    set_umi_ex(&cmd, ex);

    return cmd;
}

static inline void umi_unpack(uint32_t cmd, uint32_t& opcode, uint32_t& atype, uint32_t& size,
    uint32_t& len, uint32_t& eom, uint32_t& eof, uint32_t& qos, uint32_t& prot, uint32_t& ex) {

    opcode = umi_opcode(cmd);
    size = umi_size(cmd);
    len = umi_len(cmd);
    atype = umi_atype(cmd);
    qos = umi_qos(cmd);
    prot = umi_prot(cmd);
    eom = umi_eom(cmd);
    eof = umi_eof(cmd);
    ex = umi_ex(cmd);
}

static inline void umi_unpack(uint32_t cmd, uint32_t& opcode, uint32_t& atype, uint32_t& size,
    uint32_t& len, uint32_t& eom, uint32_t& eof) {
    uint32_t qos, prot, ex;
    umi_unpack(cmd, opcode, atype, size, len, eom, eof, qos, prot, ex);
}

static inline void umi_unpack(uint32_t cmd, uint32_t& opcode, uint32_t& atype, uint32_t& size,
    uint32_t& len, uint32_t& eom, uint32_t& eof, uint32_t& qos) {
    uint32_t prot, ex;
    umi_unpack(cmd, opcode, atype, size, len, eom, eof, qos, prot, ex);
}

static inline void umi_unpack(uint32_t cmd, uint32_t& opcode, uint32_t& atype, uint32_t& size,
    uint32_t& len, uint32_t& eom, uint32_t& eof, uint32_t& qos, uint32_t& prot) {
    uint32_t ex;
    umi_unpack(cmd, opcode, atype, size, len, eom, eof, qos, prot, ex);
}

static inline std::string umi_opcode_to_str(uint32_t cmd) {
    uint32_t opcode = umi_opcode(cmd);
    if (opcode == UMI_INVALID) {
        return "UMI_INVALID";
    } else if (opcode == UMI_REQ_READ) {
        return "UMI_REQ_READ";
    } else if (opcode == UMI_REQ_RDMA) {
        return "UMI_REQ_RDMA";
    } else if (opcode == UMI_REQ_WRITE) {
        return "UMI_REQ_WRITE";
    } else if (opcode == UMI_REQ_POSTED) {
        return "UMI_REQ_POSTED";
    } else if (opcode == UMI_REQ_ATOMIC) {
        return "UMI_REQ_ATOMIC";
    } else if (opcode == UMI_RESP_READ) {
        return "UMI_RESP_READ";
    } else if (opcode == UMI_RESP_WRITE) {
        return "UMI_RESP_WRITE";
    } else if (opcode == UMI_REQ_ATOMIC) {
        uint32_t atomic = umi_atype(cmd);
        if (atomic == UMI_REQ_ATOMICADD) {
            return "UMI_REQ_ATOMICADD";
        } else if (atomic == UMI_REQ_ATOMICAND) {
            return "UMI_REQ_ATOMICAND";
        } else if (atomic == UMI_REQ_ATOMICOR) {
            return "UMI_REQ_ATOMICOR";
        } else if (atomic == UMI_REQ_ATOMICXOR) {
            return "UMI_REQ_ATOMICXOR";
        } else if (atomic == UMI_REQ_ATOMICMAX) {
            return "UMI_REQ_ATOMICMAX";
        } else if (atomic == UMI_REQ_ATOMICMIN) {
            return "UMI_REQ_ATOMICMIN";
        } else if (atomic == UMI_REQ_ATOMICMAXU) {
            return "UMI_REQ_ATOMICMAXU";
        } else if (atomic == UMI_REQ_ATOMICMINU) {
            return "UMI_REQ_ATOMICMINU";
        } else if (atomic == UMI_REQ_ATOMICSWAP) {
            return "UMI_REQ_ATOMICSWAP";
        } else {
            return "UMI_REQ_ATOMIC";
        }
    } else if (is_umi_user(opcode)) {
        return "UMI_USER";
    } else if (is_umi_future(opcode)) {
        return "UMI_FUTURE";
    } else {
        return "UMI_UNKNOWN";
    }
}

#endif // __UMILIB_HPP__
