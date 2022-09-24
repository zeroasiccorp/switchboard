#ifndef __SWITCHBOARD_HPP__
#define __SWITCHBOARD_HPP__

#include <boost/lockfree/spsc_queue.hpp>
#include <boost/interprocess/managed_shared_memory.hpp>

#include <array>
#include <cstdio>
#include <thread>
#include <vector>

namespace bip = boost::interprocess;

// packet type
// TODO: make size runtime programmable
#define SB_DATA_SIZE 32
struct sb_packet {
    uint8_t data[SB_DATA_SIZE];
    uint32_t destination;
    bool last;
};

// queue type
// TODO: make queue capacity runtime programmable
#define SB_QUEUE_CAPACITY 1024
typedef boost::lockfree::spsc_queue<sb_packet, boost::lockfree::capacity<SB_QUEUE_CAPACITY> > shared_queue;

static inline shared_queue* sb_init(const char* uri, bip::managed_shared_memory& segment) {
    // allocate the memory if needed

    // TODO: add locking as in some of the development branches

    int extra_space = 4096;
    segment = bip::managed_shared_memory(bip::open_or_create, uri, sizeof(shared_queue) + extra_space);

    // find the queue
    return segment.find_or_construct<shared_queue>("q")();
}

class SBTX {
    public:
        SBTX() : m_active(false) {}

        void init(std::string uri) {
            init(uri.c_str());
        }

        void init(const char* uri) {
            m_queue = sb_init(uri, m_segment);
            m_active = true;
        }

        bool send(sb_packet& p) {
            return m_queue->push(p);
        }

        void send_blocking(sb_packet& p) {
            while(!(m_queue->push(p))) {
                std::this_thread::yield();
            }
        }

        bool all_read() {
            return (SB_QUEUE_CAPACITY == (m_queue->write_available()));
        }

        bool is_active() {
            return m_active;
        }
    private:
        bool m_active;
        bip::managed_shared_memory m_segment;
        shared_queue* m_queue;
};

class SBRX {
    public:
        SBRX() : m_active(false) {}

        void init(std::string uri) {
            init(uri.c_str());
        }

        void init(const char* uri) {
            m_queue = sb_init(uri, m_segment);
            m_active = true;
        }

        bool recv(sb_packet& p) {
            return m_queue->pop(p);
        }

        bool recv() {
            return m_queue->pop();
        }

        void recv_blocking(sb_packet& p){
            while(!(m_queue->pop(p))) {
                std::this_thread::yield();
            }
        }

        bool recv_peek(sb_packet& p) {
            size_t avail = m_queue->read_available();
            if (avail > 0) {
                p = m_queue->front();
            }
            return avail;
        }

        bool is_active() {
            return m_active;
        }
    private:
        bool m_active;
        bip::managed_shared_memory m_segment;
        shared_queue* m_queue;
};

static inline void delete_shared_queue(const char* name) {    
    bip::shared_memory_object::remove(name);
}

static inline void delete_shared_queue(std::string name) {    
    delete_shared_queue(name.c_str());
}

static inline std::string sb_packet_to_str(sb_packet p) {
    // used for convenient formatting with sprintf
    char buf[128];

    // build up return value
    std::string retval;
    retval = "";

    // format control information
    sprintf(buf, "dest: %08x, last: %d, data: {", p.destination, p.last);
    retval += buf;

    // format data
    for (int i=0; i<sizeof(p.data); i++) {
        sprintf(buf, "%02x", p.data[i]);
        retval += buf;
        if (i != (sizeof(p.data)-1)) {
            retval += ", ";
        }
    }

    retval += "}";

    return retval;
}

#endif // __SWITCHBOARD_HPP__
