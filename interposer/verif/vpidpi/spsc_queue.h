#ifndef __SPSC_QUEUE__
#define __SPSC_QUEUE__

#include <stdatomic.h>
#include <sys/mman.h>

#define BUFFER_ENTRIES 2000
#define PACKET_SIZE 32

typedef struct spsc_queue {
    atomic_int count;
    int packets[BUFFER_ENTRIES][PACKET_SIZE];
} spsc_queue;

static inline spsc_queue* spsc_open(char* name) {
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

static inline int spsc_recv(spsc_queue* q, int* buf, int* ptr) {
    if (atomic_load(&(q->count)) > 0) {
        // move data
        memcpy(buf, q->packets[*ptr], sizeof(int)*PACKET_SIZE);

        // update pointer
        *ptr = ((*ptr)+1)%BUFFER_ENTRIES;

        // update count of data
        atomic_fetch_add(&(q->count), -1);

        // indicate success
        return 1;
    } else {
        // indicate failure
        return 0;
    }
}

static inline int spsc_send(spsc_queue *q, const int* buf, int* ptr) {
    if (atomic_load(&(q->count)) < BUFFER_ENTRIES) {
        // move data
        memcpy(q->packets[*ptr], buf, sizeof(int)*PACKET_SIZE);

        // update pointer
        *ptr = ((*ptr)+1)%BUFFER_ENTRIES;

        // update count of data
        atomic_fetch_add(&(q->count), +1);

        // indicate succcess
        return 1;
    } else {
        // indicate failure
        return 0;
    }
}

#endif // _SPSC_QUEUE