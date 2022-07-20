#ifndef __SPSC_QUEUE__
#define __SPSC_QUEUE__

#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#define SPSC_QUEUE_CAPACITY_BYTES 32768
#define SPSC_QUEUE_CACHE_LINE_SIZE 64

typedef struct spsc_queue {
    uint8_t buf[SPSC_QUEUE_CAPACITY_BYTES];
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

static inline int spsc_send(spsc_queue *q, const uint8_t* buf, int n) {
    // get pointer to head
    int head;
    __atomic_load(&q->head, &head, __ATOMIC_RELAXED);

    // do an initial check to make sure there's enough free space
    int used_space = head - q->cached_tail;
    if (used_space < 0) {
        used_space += SPSC_QUEUE_CAPACITY_BYTES;
    }
    int free_space = SPSC_QUEUE_CAPACITY_BYTES - 1 - used_space;

    // if that fails, read the latest tail pointer and check again
    if (free_space < n) {
        __atomic_load(&q->tail, &q->cached_tail, __ATOMIC_ACQUIRE);
        used_space = head - q->cached_tail;
        if (used_space < 0) {
            used_space += SPSC_QUEUE_CAPACITY_BYTES;
        }
        free_space = SPSC_QUEUE_CAPACITY_BYTES - 1 - used_space;
        if (free_space < n) {
            return 0;
        }
    }

    // copy in the bytes in one or two parts
    if ((head + n) <= SPSC_QUEUE_CAPACITY_BYTES) {
        memcpy(&(q->buf[head]), buf, n);
    } else {
        int first_part = SPSC_QUEUE_CAPACITY_BYTES - head;
        memcpy(&(q->buf[head]), buf, first_part);
        memcpy(&(q->buf[0]), buf, n - first_part);
    }

    // and update the write pointer
    head += n;
    if (head >= SPSC_QUEUE_CAPACITY_BYTES) {
        head -= SPSC_QUEUE_CAPACITY_BYTES;
    }
    __atomic_store(&q->head, &head, __ATOMIC_RELEASE);

    return 1;
}

static inline int spsc_recv(spsc_queue* q, uint8_t* buf, int n) {
    // get the read pointer
    int tail;
    __atomic_load(&q->tail, &tail, __ATOMIC_RELAXED);

    // do an initial check to make sure there's enough data to receive
    int used_space = q->cached_head - tail;
    if (used_space < 0) {
        used_space += SPSC_QUEUE_CAPACITY_BYTES;
    }

    // if that fails, read the latest head pointer and check again
    if (used_space < n) {
        __atomic_load(&q->head, &q->cached_head, __ATOMIC_ACQUIRE);
        used_space = q->cached_head - tail;
        if (used_space < 0) {
            used_space += SPSC_QUEUE_CAPACITY_BYTES;
        }        
        if (used_space < n) {
            return 0;
        }
    }

    // copy out the bytes in one or two parts
    if ((tail + n) <= SPSC_QUEUE_CAPACITY_BYTES) {
        memcpy(buf, &(q->buf[tail]), n);
    } else {
        int first_part = SPSC_QUEUE_CAPACITY_BYTES - tail;
        memcpy(buf, &(q->buf[tail]), first_part);
        memcpy(buf + first_part, &(q->buf[0]), n - first_part);
    }

    // and update the read pointer
    tail += n;
    if (tail >= SPSC_QUEUE_CAPACITY_BYTES) {
        tail -= SPSC_QUEUE_CAPACITY_BYTES;
    }
    __atomic_store(&q->tail, &tail, __ATOMIC_RELEASE);

    return 1;
}

static inline void spsc_to_recv_contiguous(spsc_queue* q, int* n, uint8_t** buf) {
    // get the read pointer
    int tail;
    __atomic_load(&q->tail, &tail, __ATOMIC_RELAXED);

    if (tail > q->cached_head) {
        // no need to even update the cached head, since we know
        // that there is a contiguous segment to the end of the buffer
        *n = SPSC_QUEUE_CAPACITY_BYTES - tail;
    } else {
        __atomic_load(&q->head, &q->cached_head, __ATOMIC_ACQUIRE);
        *n = (q->cached_head - tail);
    }

    *buf = &(q->buf[tail]);
}

static inline void spsc_mark_received(spsc_queue* q, int n) {
    // get the read pointer
    int tail;
    __atomic_load(&q->tail, &tail, __ATOMIC_RELAXED);

    // and update the read pointer
    tail += n;
    if (tail >= SPSC_QUEUE_CAPACITY_BYTES) {
        tail -= SPSC_QUEUE_CAPACITY_BYTES;
    }

    __atomic_store(&q->tail, &tail, __ATOMIC_RELEASE);
}

static inline void spsc_to_send_contiguous(spsc_queue* q, int* n, uint8_t** buf) {
    // get the read pointer
    int head;
    __atomic_load(&q->head, &head, __ATOMIC_RELAXED);
    __atomic_load(&q->tail, &q->cached_tail, __ATOMIC_ACQUIRE);

    // find out how much free space there is
    int used_space = head - q->cached_tail;
    if (used_space < 0) {
        used_space += SPSC_QUEUE_CAPACITY_BYTES;
    }
    int free_space = SPSC_QUEUE_CAPACITY_BYTES - 1 - used_space;

    if ((head + free_space) <= SPSC_QUEUE_CAPACITY_BYTES) {
        *n = free_space;
    } else {
        *n = SPSC_QUEUE_CAPACITY_BYTES - head;
    }

    *buf = &(q->buf[head]);
}

static inline void spsc_mark_sent(spsc_queue* q, int n) {
    // get the read pointer
    int head;
    __atomic_load(&q->head, &head, __ATOMIC_RELAXED);

    // and update the read pointer
    head += n;
    if (head >= SPSC_QUEUE_CAPACITY_BYTES) {
        head -= SPSC_QUEUE_CAPACITY_BYTES;
    }

    __atomic_store(&q->head, &head, __ATOMIC_RELEASE);
}

#endif // _SPSC_QUEUE