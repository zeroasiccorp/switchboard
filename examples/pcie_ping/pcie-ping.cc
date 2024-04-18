// Switchboard PCIe ping example.

// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#include "switchboard_pcie.hpp"

static void usage(const char* progname) {
    printf("%s: BDF BAR-num offset\n\n", progname);
}

static void bad_queue(const char* name) {
    assert(name);
    printf("Unable to initialize PCIe %s-queue!\n", name);
    exit(EXIT_FAILURE);
}

int main(int argc, char* argv[]) {
    const char* bdf;
    int bar_num;
    SBTX_pcie tx(0);
    SBRX_pcie rx(1);
    int i;
    struct timespec start, end;

    if (argc < 2) {
        usage(argv[0]);
        return EXIT_FAILURE;
    }

    bdf = argv[1];
    bar_num = 0;

    if (!tx.init("queue-tx", bdf, bar_num)) {
        bad_queue("tx");
    }
    if (!rx.init("queue-rx", bdf, bar_num)) {
        bad_queue("rx");
    }

    for (i = 0; i < 1024; i++) {
        sb_packet p = {0};

        printf("ping %d\n", i);
        clock_gettime(CLOCK_MONOTONIC, &start);
        while (!tx.send(p)) {}
        while (!rx.recv(p)) {}
        clock_gettime(CLOCK_MONOTONIC, &end);

        double tdiff = (end.tv_sec - start.tv_sec) + 1e-9 * (end.tv_nsec - start.tv_nsec);
        printf("latency: %f sec\n", tdiff);
    }

    delete_shared_queue("queue-tx");
    delete_shared_queue("queue-rx");
    return 0;
}
