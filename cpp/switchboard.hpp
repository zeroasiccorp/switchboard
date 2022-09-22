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

enum UMI_CMD {UMI_WRITE_NORMAL=0b00000001, UMI_READ=0b00001000};

static inline void umi_pack(umi_packet& p, uint32_t opcode, uint32_t size, uint32_t user,
    uint64_t dstaddr, uint64_t srcaddr, uint32_t data[], bool burst=false) {

    if (burst) {
        // populate the packet
        p[7] = data[4];
        p[6] = data[3];
        p[5] = data[2];
        p[4] = data[1];
        p[3] = data[0];
        p[2] = data[7];
        p[1] = data[6];
        p[0] = data[5];
    } else {
        // determine if this is a read command
        bool cmd_read = (opcode >> 3) & 0b1;

        // form the 32-bit command
        uint32_t cmd_out = 0;
        cmd_out |= (opcode & 0xff);
        cmd_out |= (size & 0xf) << 8;
        cmd_out |= (user & 0xfffff) << 12;

        // populate the packet
        p[7] = (dstaddr >> 32) & 0xffffffff;
        if (cmd_read) {
            p[6] = (srcaddr >> 32) & 0xffffffff;
        } else {
            // size=4 corresponds to 16 bytes (128 bits) of data
            p[6] = (size >= 4) ? data[3] : 0;
        }
        p[5] = (size >= 4) ? data[2] : 0;  // size=4 corresponds to 16 bytes (128 bits) of data
        p[4] = (size >= 3) ? data[1] : 0;  // size=3 corresponds to 8 bytes (64 bits) of data
        p[3] = data[0];
        p[2] = srcaddr & 0xffffffff;
        p[1] = dstaddr & 0xffffffff;
        p[0] = cmd_out;
    }
}

static inline void umi_pack(umi_packet& p, uint32_t opcode, uint64_t dstaddr,
    uint64_t srcaddr, uint64_t data, uint32_t user=0) {
    
    // format the data as 32-bit words
    uint32_t data_arr[2];
    data_arr[1] = (data >> 32) & 0xffffffff;
    data_arr[0] = data & 0xffffffff;

    // size=3 means than 2^3=8 bytes (64 bits) are sent
    umi_pack(p, opcode, 3, user, dstaddr, srcaddr, data_arr);
}

static inline void umi_pack(umi_packet& p, uint32_t opcode, uint64_t dstaddr,
    uint64_t srcaddr, uint32_t data, uint32_t user=0) {
    
    // size=2 means than 2^2=4 bytes (32 bits) are sent
    umi_pack(p, opcode, 2, user, dstaddr, srcaddr, &data);
}

static inline void umi_unpack(const umi_packet& p, uint32_t& opcode, uint32_t& size, uint32_t& user,
    uint64_t& dstaddr, uint64_t& srcaddr, uint32_t data[], bool burst=false) {

    if (burst) {
        // unpack only the data
        data[0] = p[3];
        data[1] = p[4];
        data[2] = p[5];
        data[3] = p[6];
        data[4] = p[7];
        data[5] = p[0];
        data[6] = p[1];
        data[7] = p[2];
    } else {
        // unpack the 32-bit command
        opcode = p[0] & 0xff;
        size = (p[0] >> 8) & 0xf;
        user = (p[0] >> 12) & 0xfffff;

        // determine destination address
        dstaddr = 0;
        dstaddr |= p[7];
        dstaddr <<= 32;
        dstaddr |= p[1];

        // determine the source address (only valid for a read)
        srcaddr = 0;
        srcaddr |= p[6];
        srcaddr <<= 32;
        srcaddr |= p[2];

        // copy out the data
        data[0] = p[3];
        data[1] = p[4];
        data[2] = p[5];
        data[3] = p[6];
    }
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

static inline std::string umi_opcode_to_str(uint32_t opcode) {
    if (opcode == 0b00000000) {
        return "INVALID";
    } else if ((opcode & 0b1111) == 0b0001) {
        return "WRITE-NORMAL";
    } else if ((opcode & 0b1111) == 0b0010) {
        return "WRITE-RESPONSE";
    } else if ((opcode & 0b1111) == 0b0011) {
        return "WRITE-SIGNAL";
    } else if ((opcode & 0b1111) == 0b0100) {
        return "WRITE-STREAM";
    } else if ((opcode & 0b1111) == 0b0101) {
        return "WRITE-ACK";
    } else if ((opcode & 0b1110) == 0b0110) {
        return "USER";
    } else if (opcode == 0b00001000) {
        return "READ";
    } else if (opcode == 0b00001001) {
        return "ATOMIC-SWAP";
    } else if (opcode == 0b00011001) {
        return "ATOMIC-ADD";
    } else if (opcode == 0b00101001) {
        return "ATOMIC-AND";
    } else if (opcode == 0b00111001) {
        return "ATOMIC-OR";
    } else if (opcode == 0b01001001) {
        return "ATOMIC-XOR";
    } else if (opcode == 0b01011001) {
        return "ATOMIC-MAX";
    } else if (opcode == 0b01101001) {
        return "ATOMIC-MIN";
    } else if ((opcode & 0b10001111) == 0b10001001) {
        return "ATOMIC-USER";
    } else if ((opcode & 0b1111) == 0b1011) {
        return "USER";
    } else if ((opcode & 0b1111) == 0b1100) {
        return "USER";
    } else if ((opcode & 0b1111) == 0b1101) {
        return "USER";
    } else if ((opcode & 0b1111) == 0b1110) {
        return "USER";
    } else if ((opcode & 0b1111) == 0b1111) {
        return "USER";
    } else {
        return "UNKNOWN";
    }
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
