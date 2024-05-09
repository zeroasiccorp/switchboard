// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#ifndef __SWITCHBOARD_HPP__
#define __SWITCHBOARD_HPP__

#include <array>
#include <chrono>
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

static inline long max_rate_timestamp_us() {
    return std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch())
        .count();
}

static inline void max_rate_tick(long& last_us, long min_period_us) {
    if (min_period_us > 0) {
        // measure the time now

        long now_us = max_rate_timestamp_us();

        // sleep if needed

        if (last_us != -1) {
            long dt_us = now_us - last_us;

            if (dt_us < min_period_us) {
                long sleep_us = min_period_us - dt_us;
                std::this_thread::sleep_for(std::chrono::microseconds(sleep_us));
            }
        }

        // update the time stamp.  it is not enough to set last_us = now_us,
        // due to the sleep_for invocation

        last_us = max_rate_timestamp_us();
    }
}

static inline void start_delay(double value) {
    if (value > 0) {
        int value_us = (value * 1.0e6) + 0.5;
        std::this_thread::sleep_for(std::chrono::microseconds(value_us));
    }
}

class SB_base {
  public:
    SB_base() : m_active(false), m_q(NULL) {}

    virtual ~SB_base() {
        deinit();
    }

    void init(std::string uri, size_t capacity = 0, bool fresh = false, double max_rate = -1) {
        init(uri.c_str(), capacity, fresh, max_rate);
    }

    void init(const char* uri, size_t capacity = 0, bool fresh = false, double max_rate = -1) {
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
        m_timestamp_us = -1;

        set_max_rate(max_rate);
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

    void set_max_rate(double max_rate) {
        if (max_rate > 0) {
            m_min_period_us = (1.0e6 / max_rate) + 0.5;
        } else {
            m_min_period_us = -1;
        }
    }

  protected:
    void check_active(void) {
        if (!m_active) {
            throw std::runtime_error("Using an uninitialized SB queue!");
        }
    }

    bool m_auto_deinit;
    bool m_active;
    long m_min_period_us;
    long m_timestamp_us;
    spsc_queue* m_q;
};

class SBTX : public SB_base {
  public:
    SBTX() {}

    bool send(sb_packet& p) {
        check_active();
        max_rate_tick(m_timestamp_us, m_min_period_us);
        return spsc_send(m_q, &p, sizeof p);
    }

    void send_blocking(sb_packet& p) {
        bool success = false;

        while (!success) {
            success = send(p);

            if ((!success) && (m_min_period_us == -1)) {
                // maintain old behavior if max_rate isn't specified,
                // i.e. yield on every iteration that the send isn't
                // successful
                std::this_thread::yield();
            }
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
        max_rate_tick(m_timestamp_us, m_min_period_us);
        return spsc_recv(m_q, &p, sizeof p);
    }

    bool recv() {
        check_active();
        sb_packet dummy_p;
        max_rate_tick(m_timestamp_us, m_min_period_us);
        return spsc_recv(m_q, &dummy_p, sizeof dummy_p);
    }

    void recv_blocking(sb_packet& p) {
        bool success = false;

        while (!success) {
            success = recv(p);

            if ((!success) && (m_min_period_us == -1)) {
                // maintain old behavior if max_rate isn't specified,
                // i.e. yield on every iteration that the send isn't
                // successful
                std::this_thread::yield();
            }
        }
    }

    bool recv_peek(sb_packet& p) {
        check_active();
        max_rate_tick(m_timestamp_us, m_min_period_us);
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
