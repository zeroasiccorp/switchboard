// Copyright (c) 2023 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "switchboard.hpp"

int main(int argc, char* argv[]) {
    // determine communication method

    int arg_idx = 1;

    bool is_tx = false;
    if (arg_idx < argc) {
        const char* arg = argv[arg_idx++];
        if (strcmp(arg, "-") == 0) {
            // use default
        } else if (strcmp(arg, "tx") == 0) {
            is_tx = true;
        } else if (strcmp(arg, "rx") == 0) {
            is_tx = false;
        } else {
            fprintf(stderr, "Unknown argument: %s\n", arg);
            exit(1);
        }
    }

    const char* arg = "5555";
    if (arg_idx < argc) {
        arg = argv[arg_idx++];
    }
    char port[128];
    sprintf(port, "queue-%s", arg);

    int iterations = 10000000;
    if (arg_idx < argc) {
        const char* arg = argv[arg_idx++];
        if (strcmp(arg, "-") != 0) {
            iterations = atoi(arg);
        }
    }

    if (is_tx) {
        // initialize TX
        SBTX tx;
        tx.init(port);

        // initialize the packet
        sb_packet p = {0};
        p.data[0] = 1;

        // send pseudo-random data
        int count = 0;
        while (count < iterations) {
            if (tx.send(p)) {
                // increment element index
                count++;

                // rotate pattern
                uint8_t tmp = p.data[31];
                for (int i = 31; i > 0; i--) {
                    p.data[i] = p.data[i - 1];
                }
                p.data[0] = tmp;
            }
        }
    } else {
        int count = 0;
        uint32_t out = 0;
        sb_packet p;

        // initialize RX
        SBRX rx;
        rx.init(port);

        // start measuring time taken
        std::chrono::steady_clock::time_point start_time = std::chrono::steady_clock::now();

        while (count < iterations) {
            if (rx.recv(p)) {
                count++;
                for (int i = 0; i < 32; i++) {
                    out += p.data[i];
                }
            }
        }

        // print output to make sure it is not optimized away
        printf("Output: %d\n", out);

        // stop measuring time taken
        std::chrono::steady_clock::time_point stop_time = std::chrono::steady_clock::now();
        double t =
            1.0e-6 *
            (std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());

        // print bandwidth
        double rate = (1.0 * iterations) / t;
        printf("Rate: %0.3f MT/s\n", rate * 1e-6);
    }

    return 0;
}
