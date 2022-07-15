#ifndef __SPSC_QUEUE__
#define __SPSC_QUEUE__

#include <boost/lockfree/spsc_queue.hpp>
#include <boost/interprocess/managed_shared_memory.hpp>
#include <array>

#define PACKET_SIZE 32
#define QUEUE_CAPACITY 1000
#define SHMEM_SIZE 262144

namespace bip = boost::interprocess;
typedef std::array<int, PACKET_SIZE> packet;
typedef boost::lockfree::spsc_queue<packet, boost::lockfree::capacity<QUEUE_CAPACITY>> ring_buffer;

static inline ring_buffer* spsc_open(bip::managed_shared_memory& segment, char* name) {
    segment = bip::managed_shared_memory(bip::open_or_create, name, 262144);
    return segment.find_or_construct<ring_buffer>("queue")();
}

#endif // _SPSC_QUEUE