#ifndef __UMI_INTF__
#define __UMI_INTF__

#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include "spsc_queue.h"
#include <sched.h>
#include <errno.h>

typedef enum umi_mode {
    UMI_QUEUE=0,
    UMI_TCP=1,
    UMI_PCIE=2
} umi_mode;

typedef struct thread_arg {
    char* uri;
    spsc_queue* q;
    bool is_tx;
} thread_arg;

int tcp_try_connect(int* sockfd, struct sockaddr_in* serv_addr) {
    *sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (*sockfd < 0) {
        fprintf(stderr, "ERROR opening socket\n");
        exit(1);
    }
    return connect(*sockfd, (struct sockaddr *)serv_addr, sizeof(struct sockaddr_in));
}

void tcp_write_loop(struct sockaddr_in* serv_addr, spsc_queue* q) {
    int sockfd;
    while (tcp_try_connect(&sockfd, serv_addr) < 0){
        close(sockfd);
        sched_yield();
    }

    int n;
    uint32_t* buf;
    while (1) {
        // receive packets into a buffer
        spsc_to_recv_contiguous(q, &n, &buf);

        // send packets over the socket
        if (n > 0) {
            write(sockfd, buf, sizeof(uint32_t)*SPSC_QUEUE_PACKET_SIZE*n);
            spsc_mark_received(q, n);
        } else {
            sched_yield();
        }
    }
}

void tcp_read_loop(struct sockaddr_in* serv_addr, spsc_queue* q, int port) {
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        fprintf(stderr, "ERROR opening socket\n");
        exit(1);
    }

    const int enable = 1;
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int)) < 0) {
        fprintf(stderr, "setsockopt(SO_REUSEADDR) failed\n");
        exit(1);
    }
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, &enable, sizeof(int)) < 0) {
        fprintf(stderr, "setsockopt(SO_REUSEADDR) failed\n");
        exit(1);
    }

    if (bind(sockfd, (struct sockaddr *)serv_addr, sizeof(struct sockaddr_in)) < 0) {
        fprintf(stderr, "ERROR on binding.\n");
        exit(1);
    }

    // start listening
    listen(sockfd, 5);

    struct sockaddr_in cli_addr;
    socklen_t clilen = sizeof(cli_addr);
    int newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
    if (newsockfd < 0) {
        fprintf(stderr, "ERROR on accept\n");
        exit(1);
    }

    // read from socket
    int off = 0;
    int n;
    uint32_t buf[SPSC_QUEUE_CAPACITY][SPSC_QUEUE_PACKET_SIZE];
    while (1) {
        // receive packets into a buffer
        uint8_t* ptr = (uint8_t*)(buf[0]) + off;
        int n_bytes = read(newsockfd, ptr, (sizeof(uint32_t)*SPSC_QUEUE_PACKET_SIZE*SPSC_QUEUE_CAPACITY) - off);
        
        // send all complete packets
        int n_packets = n_bytes / (sizeof(uint32_t)*SPSC_QUEUE_PACKET_SIZE);
        for (int i=0; i<n_packets; i++) {
            while(spsc_send(q, buf[i]) == 0) {
                sched_yield();
            }
        }
        
        // deal with packet tearing
        off = n_bytes - (n_packets*sizeof(uint32_t)*SPSC_QUEUE_PACKET_SIZE);
        if ((off != 0) && (n_packets >= 1)) {
            memcpy(buf[0], buf[n_packets], off);
        }
    }
}

void* tcp_thread(void* arg) {
    // extract arguments
    thread_arg* ptr = (thread_arg*)arg;
    char* uri = ptr->uri;
    spsc_queue* q = ptr->q;
    bool is_tx = ptr->is_tx;

    // split into IP address and port
    // TODO cleanup
    char ip_addr[16] = {0};
    char port[6] = {0};
    char* delim = strstr(uri, ":");
    memcpy(ip_addr, uri, delim-uri);
    memcpy(port, delim+1, strlen(uri)-(delim-uri)-1);

    struct sockaddr_in serv_addr = {0};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(atoi(port));
    if (is_tx) {
        // client
        in_addr_t s_addr = inet_addr(ip_addr);
        if (s_addr == -1) {
            fprintf(stderr, "ERROR, no such host\n");
            exit(1);
        }
        serv_addr.sin_addr.s_addr = s_addr;

        tcp_write_loop(&serv_addr, q);        
    } else {
        // server
        serv_addr.sin_addr.s_addr = INADDR_ANY;

        tcp_read_loop(&serv_addr, q, atoi(port));
    }

    return NULL;
}

static inline spsc_queue* umi_init(const char* uri, bool is_tx, umi_mode mode) {
    if (mode == UMI_QUEUE) {
        return spsc_open(uri);
    } else if (mode == UMI_TCP) {
        // allocate queue
        spsc_queue* q = (spsc_queue*)malloc(sizeof(spsc_queue));
        memset(q, 0, sizeof(spsc_queue));

        // fill in arguments for thread
        thread_arg* arg = (thread_arg*)malloc(sizeof(thread_arg));
        arg->uri = (char*)malloc(strlen(uri)+1);
        memcpy(arg->uri, uri, strlen(uri)+1);
        arg->q = q;
        arg->is_tx = is_tx;

        pthread_t tid;
        pthread_create(&tid, NULL, &tcp_thread, (void*)arg);

        // return queue
        return q;
    } else if (mode == UMI_PCIE) {
        fprintf(stderr, "PCIe is not supported yet.\n");
        exit(1);
    } else {
        fprintf(stderr, "Unsupported mode.\n");
        exit(1);
    }
}

#endif // __UMI_INTF__