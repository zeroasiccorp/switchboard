#ifndef __SPSC_QUEUE__
#define __SPSC_QUEUE__

#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#define SPSC_QUEUE_CAPACITY 1000
#define SPSC_QUEUE_PACKET_SIZE 8
#define SPSC_QUEUE_CACHE_LINE_SIZE 64

typedef struct spsc_queue {
    uint32_t packets[SPSC_QUEUE_CAPACITY][SPSC_QUEUE_PACKET_SIZE];
    int head __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    int cached_tail __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    int tail __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    int cached_head __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
} spsc_queue;

static inline spsc_queue* spsc_open(const char* name) {
    int fd = open(name, O_RDWR);
    return (spsc_queue*)mmap(
        NULL,
        sizeof(spsc_queue),
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        fd,
        0
	);
}

static inline int spsc_send(spsc_queue *q, const uint32_t* buf) {
    // get pointer to head
    int head;
    __atomic_load(&q->head, &head, __ATOMIC_RELAXED);

    // compute the head pointer
    int next_head = head + 1;
    if (next_head == SPSC_QUEUE_CAPACITY) {
        next_head = 0;
    }

    // if the queue is full, bail out
    if (next_head == q->cached_tail) {
        __atomic_load(&q->tail, &q->cached_tail, __ATOMIC_ACQUIRE);
        if (next_head == q->cached_tail) {
            return 0;
        }
    }

    // otherwise write in the packet
    memcpy(q->packets[head], buf, 32);

    // and update the head pointer
    __atomic_store(&q->head, &next_head, __ATOMIC_RELEASE);

    return 1;
}

static inline int spsc_recv(spsc_queue* q, uint32_t* buf) {
    // get the read pointer
    int tail;
    __atomic_load(&q->tail, &tail, __ATOMIC_RELAXED);

    // if the queue is empty, bail out
    if (tail == q->cached_head) {
        __atomic_load(&q->head, &q->cached_head, __ATOMIC_ACQUIRE);
        if (tail == q->cached_head) {
            return 0;
        }
    }

    // otherwise read out the packet
    memcpy(buf, q->packets[tail], 32);

    // and update the read pointer
    tail++;
    if (tail == SPSC_QUEUE_CAPACITY) {
        tail = 0;
    }
    __atomic_store(&q->tail, &tail, __ATOMIC_RELEASE);

    return 1;
}

#endif // _SPSC_QUEUE