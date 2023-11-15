// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __SWITCHBOARD_HPP__
#define __SWITCHBOARD_HPP__

#include <array>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include "spsc_queue.h"

// packet type
// TODO: make size runtime programmable
#define SB_DATA_SIZE 52
struct sb_packet {
    uint32_t destination;
    union {
        struct {
            unsigned int last : 1;
        };
        uint32_t flags;
    };
    uint8_t data[SB_DATA_SIZE];
} __attribute__((packed));

class SB_base {
  public:
    SB_base() : m_active(false), m_q(NULL) {}

    virtual ~SB_base() {
        deinit();
    }

    void init(std::string uri, size_t capacity = 0, bool fresh = false) {
        init(uri.c_str(), capacity, fresh);
    }

    void init(const char* uri, size_t capacity = 0, bool fresh = false) {
        // Default to one page of capacity
        if (capacity == 0) {
            capacity = spsc_capacity(getpagesize());
        }

        // delete old queue if "fresh" is set
        if (fresh) {
            spsc_remove_shmfile(uri);
        }

        m_q = spsc_open(uri, capacity);
        m_active = true;
    }

    void deinit(void) {
        spsc_close(m_q);
        m_active = false;
    }

    bool is_active() {
        return m_active;
    }

    int mlock(void) {
        check_active();
        assert(m_q);
        return spsc_mlock(m_q);
    }

    int get_capacity(void) {
        check_active();
        return m_q->capacity;
    }

    void* get_shm_handle(void) {
        check_active();
        return m_q->shm;
    }

  protected:
    void check_active(void) {
        if (!m_active) {
            throw std::runtime_error("Using an uninitialized SB queue!");
        }
    }

    bool m_auto_deinit;
    bool m_active;
    spsc_queue* m_q;
};

class SBTX : public SB_base {
  public:
    SBTX() {}

    bool send(sb_packet& p) {
        check_active();
        return spsc_send(m_q, &p, sizeof p);
    }

    void send_blocking(sb_packet& p) {
        while (!send(p)) {
            std::this_thread::yield();
        }
    }

    bool all_read() {
        check_active();
        return spsc_size(m_q) == 0;
    }
};

class SBRX : public SB_base {
  public:
    SBRX() {}

    bool recv(sb_packet& p) {
        check_active();
        return spsc_recv(m_q, &p, sizeof p);
    }

    bool recv() {
        check_active();
        sb_packet dummy_p;
        return spsc_recv(m_q, &dummy_p, sizeof dummy_p);
    }

    void recv_blocking(sb_packet& p) {
        while (!recv(p)) {
            std::this_thread::yield();
        }
    }

    bool recv_peek(sb_packet& p) {
        check_active();
        return spsc_recv_peek(m_q, &p, sizeof p);
    }
};

static inline void delete_shared_queue(const char* name) {
    spsc_remove_shmfile(name);
}

static inline void delete_shared_queue(std::string name) {
    delete_shared_queue(name.c_str());
}

static inline std::string sb_packet_to_str(sb_packet p, ssize_t nbytes = -1) {
    // determine how many bytes to print
    size_t max_idx;
    if (nbytes < 0) {
        max_idx = sizeof(p.data);
    } else {
        max_idx = nbytes;
    }

    // used for convenient formatting with sprintf
    char buf[128];

    // build up return value
    std::string retval;
    retval = "";

    // format control information
    sprintf(buf, "dest: %08x, last: %d, data: {", p.destination, p.last);
    retval += buf;

    // format data
    for (size_t i = 0; i < max_idx; i++) {
        sprintf(buf, "%02x", p.data[i]);
        retval += buf;
        if (i != (max_idx - 1)) {
            retval += ", ";
        }
    }

    retval += "}";

    return retval;
}

#endif // __SWITCHBOARD_HPP__
