#ifndef __UMIVERSE_HPP__
#define __UMIVERSE_HPP__

#include <boost/lockfree/spsc_queue.hpp>
#include <boost/interprocess/managed_shared_memory.hpp>

#include <array>
#include <cstdio>

namespace bip = boost::interprocess;

// packet type
typedef std::array<uint32_t, 8> umi_packet;

// queue type
typedef boost::lockfree::spsc_queue<umi_packet, boost::lockfree::capacity<1024> > shared_queue;

class UmiConnection {
    public:
        UmiConnection() : active(false) {}
        void init(const char* uri, bool is_tx, bool is_blocking) {
            // allocate the memory if needed
            // TODO: deal with case that memory region hasn't been created
            int extra_space = 4096;
            segment = bip::managed_shared_memory(bip::open_or_create, uri, sizeof(shared_queue) + extra_space);

            // find the queue
            queue = segment.find_or_construct<shared_queue>("q")();

            // mark connection as active
            active = true;
        }

        bool send(umi_packet& p) {
            return queue->push(p);
        }

        bool recv_peek(umi_packet& p) {
            size_t avail = queue->read_available();
            if (avail > 0) {
                p = queue->front();
            }
            return avail;
        }

        bool recv(umi_packet& p) {
            return queue->pop(p);
        }

        bool recv() {
            return queue->pop();
        }

        bool is_active() {
            return active;
        }
    private:
        bool active;
        bip::managed_shared_memory segment;
        shared_queue* queue;
};

static inline void umi_pack(umi_packet& p, const uint32_t data, const uint32_t addr) {
    // only works with 32-bit data and address
    p[1] = addr;
    p[3] = data;
}

static inline void umi_unpack(const umi_packet& p, uint32_t& data, uint32_t& addr) {
    // only works with 32-bit data and address
    addr = p[1];
    data = p[3];
}

#endif // __UMIVERSE_HPP__