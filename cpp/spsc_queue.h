/*
 * Single Producer Single Consumer Queue implemented over shared-memory.
 * Copyright (C) 2022 Zero ASIC
 */

#ifndef SPSC_QUEUE_H__
#define SPSC_QUEUE_H__

#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#ifdef __cplusplus
#include <atomic>
using namespace std;
#else
#include <stdatomic.h>
#endif

#define SPSC_QUEUE_CAPACITY 1000
#define SPSC_QUEUE_PACKET_SIZE 10
#define SPSC_QUEUE_CACHE_LINE_SIZE 64

typedef struct spsc_queue {
    uint32_t packets[SPSC_QUEUE_CAPACITY][SPSC_QUEUE_PACKET_SIZE];
    int head __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    int cached_tail __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    int tail __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    int cached_head __attribute__((__aligned__(SPSC_QUEUE_CACHE_LINE_SIZE)));
    char *name;
} spsc_queue;

static inline spsc_queue* spsc_open(const char* name) {
    spsc_queue *q;
    void *p;
    int fd = -1;
    int r;

    fd = open(name, O_RDWR | O_CREAT, S_IRUSR | S_IWUSR);
    if (fd < 0) {
        perror(name);
        goto err;
    }

    r = ftruncate(fd, sizeof(spsc_queue));
    if (r < 0) {
        perror("ftruncate");
        goto err;
    }

    p = mmap(NULL, sizeof(spsc_queue),
             PROT_READ | PROT_WRITE, MAP_SHARED,
             fd, 0);

    if (p == MAP_FAILED) {
        perror("mmap");
        goto err;
    }

    // We can close the fd without affecting active mmaps.
    close(fd);

    q = (spsc_queue *) p;
    q->name = strdup(name);
    return q;

err:
    if (fd > 0) {
        close(fd);
    }
    return NULL;
}

static inline void spsc_remove_shmfile(const char *name) {
    remove(name);
}

static inline void spsc_close(spsc_queue *q) {
    // We've already closed the file-descriptor. We now need to munmap the
    // mmap and remove the the shm files.
    spsc_remove_shmfile(q->name);
    free(q->name);
    munmap(q, sizeof(spsc_queue));
}

static inline int spsc_size(spsc_queue *q) {
    int head, tail;
    int size;

    __atomic_load(&q->head, &head, __ATOMIC_ACQUIRE);
    __atomic_load(&q->tail, &tail, __ATOMIC_ACQUIRE);

    size = head - tail;
    if (size < 0) {
        size += SPSC_QUEUE_CAPACITY;
    }
    return size;
}

static inline int spsc_send(spsc_queue *q, void *buf) {
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
    memcpy(q->packets[head], buf, sizeof(uint32_t)*SPSC_QUEUE_PACKET_SIZE);

    // and update the head pointer
    __atomic_store(&q->head, &next_head, __ATOMIC_RELEASE);

    return 1;
}

static inline int spsc_recv_base(spsc_queue* q, void *buf, bool pop) {
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
    memcpy(buf, q->packets[tail], sizeof(uint32_t)*SPSC_QUEUE_PACKET_SIZE);

    if (pop) {
        // and update the read pointer
        tail++;
        if (tail == SPSC_QUEUE_CAPACITY) {
            tail = 0;
        }
        __atomic_store(&q->tail, &tail, __ATOMIC_RELEASE);
    }

    return 1;
}

static inline int spsc_recv(spsc_queue* q, void *buf) {
    return spsc_recv_base(q, buf, true);
}

static inline int spsc_recv_peek(spsc_queue* q, void *buf) {
    return spsc_recv_base(q, buf, false);
}
#endif // _SPSC_QUEUE
