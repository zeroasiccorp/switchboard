#ifndef __SWITCHBOARD_HPP__
#define __SWITCHBOARD_HPP__

#include <boost/lockfree/spsc_queue.hpp>
#include <boost/interprocess/managed_shared_memory.hpp>

#include <array>
#include <cstdio>
#include <thread>

namespace bip = boost::interprocess;

// packet type
typedef std::array<uint32_t, 8> umi_packet;

// queue type
#define UMI_QUEUE_CAPACITY 1024
typedef boost::lockfree::spsc_queue<umi_packet, boost::lockfree::capacity<UMI_QUEUE_CAPACITY> > shared_queue;

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

            // save settings
            this->is_tx = is_tx;
            this->is_blocking = is_blocking;
        }

        bool send(umi_packet& p) {
            assert(is_tx);  // must be TX
            return queue->push(p);
        }

        void send_blocking(umi_packet& p) {
            assert(is_tx && is_blocking);

            while(!(queue->push(p))) {
                std::this_thread::yield();
            }
        }

        bool recv_peek(umi_packet& p) {
            assert(!is_tx); // must be RX

            size_t avail = queue->read_available();
            if (avail > 0) {
                p = queue->front();
            }
            return avail;
        }

        bool recv(umi_packet& p) {
            assert(!is_tx);  // must be RX

            return queue->pop(p);
        }

        void recv_blocking(umi_packet& p){
            assert((!is_tx) && is_blocking);

            while(!(queue->pop(p))) {
                std::this_thread::yield();
            }
        }

        bool recv() {
            assert(!is_tx);  // must be RX

            return queue->pop();
        }

        bool is_active() {
            return active;
        }

        bool all_read() {
            assert(is_tx);  // must be TX

            return (UMI_QUEUE_CAPACITY == (queue->write_available()));
        }
    private:
        bool active;
        bool is_tx;
        bool is_blocking;
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

static inline std::string umi_packet_to_str(const umi_packet& p) {
    std::string retval = "{";

    char buf[128];
    for (int i=0; i<8; i++) {
        sprintf(buf, "0x%08x", p[i]);
        retval += buf;
        if (i != 7) {
            retval += ", ";
        }
    }

    retval += "}";

    return retval;
}

#endif // __SWITCHBOARD_HPP__
