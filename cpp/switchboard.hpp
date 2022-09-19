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
typedef std::array<uint32_t, 8> umi_packet;

// queue type
#define UMI_QUEUE_CAPACITY 1024
typedef boost::lockfree::spsc_queue<umi_packet, boost::lockfree::capacity<UMI_QUEUE_CAPACITY> > shared_queue;

class UmiConnection {
    public:
        UmiConnection() : active(false) {}

        void init(std::string uri, bool is_tx, bool is_blocking) {
            init(uri.c_str(), is_tx, is_blocking);
        }

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

static inline bool str_to_umi_packet(const char* str, umi_packet& p) {
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

static inline bool str_to_umi_packet(std::string str, umi_packet& p) {
    return str_to_umi_packet(str.c_str(), p);
}

static inline void delete_shared_queue(const char* name) {    
    bip::shared_memory_object::remove(name);
}

static inline void delete_shared_queue(std::string name) {    
    delete_shared_queue(name.c_str());
}

#endif // __SWITCHBOARD_HPP__
