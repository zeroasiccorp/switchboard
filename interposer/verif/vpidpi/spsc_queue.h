#ifndef __SPSC_QUEUE__
#define __SPSC_QUEUE__

#include <sys/mman.h>

#define BUFFER_ENTRIES 2000
#define PACKET_SIZE 32

typedef struct spsc_mmap {
    int head;
    int tail;
    int packets[BUFFER_ENTRIES][PACKET_SIZE];
} spsc_mmap;

typedef struct spsc_queue {
    int cached_head;
    int cached_tail;
    spsc_mmap* m;
} spsc_queue;

static inline void spsc_open(spsc_queue* q, char* name) {
    int fd = open(name, O_RDWR);
    q->cached_head = 0;
    q->cached_tail = 0;
    q->m = (spsc_mmap*)mmap(
        NULL,
        sizeof(spsc_queue),
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        fd,
        0
	);
}

static inline int spsc_send(spsc_queue *q, const int* buf) {
    int head;
    __atomic_load(&q->m->head, &head, __ATOMIC_RELAXED);

    if (q->cached_tail == ((head-1)%BUFFER_ENTRIES)) {
        int tail;
        __atomic_load(&q->m->tail, &tail, __ATOMIC_ACQUIRE);
        if (tail == q->cached_tail) {
            return 0;
        }
        q->cached_tail = tail;
    }

    memcpy(q->m->packets[head], buf, sizeof(int)*PACKET_SIZE);

    head = (head+1)%BUFFER_ENTRIES;
    __atomic_store(&q->m->head, &head, __ATOMIC_RELEASE);

    return 1;
}

static inline int spsc_recv(spsc_queue* q, int* buf) {
    int tail;
    __atomic_load(&q->m->tail, &tail, __ATOMIC_RELAXED);

    if (q->cached_head == tail) {
        int head;
        __atomic_load(&q->m->head, &head, __ATOMIC_ACQUIRE);
        if (head == q->cached_head) {
            return 0;
        }
        q->cached_head = head;
    }

    memcpy(buf, q->m->packets[tail], sizeof(int)*PACKET_SIZE);

    tail = (tail+1)%BUFFER_ENTRIES;
    __atomic_store(&q->m->tail, &tail, __ATOMIC_RELEASE);

    return 1;
}

#endif // _SPSC_QUEUE