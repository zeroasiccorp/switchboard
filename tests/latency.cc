// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include "switchboard.hpp"

int main(int argc, char* argv[]) {
    // determine communication method

    int arg_idx = 1;

    bool is_first = false;
    if (arg_idx < argc) {
        const char* arg = argv[arg_idx++];
        if (strcmp(arg, "second") == 0) {
            is_first = false;
        } else if (strcmp(arg, "first") == 0) {
            is_first = true;
        } else {
            printf("Ignoring argument: %s\n", arg);
        }
    }

    // determine the RX port
    const char* rx_port = "queue-0";
    if (arg_idx < argc) {
        rx_port = argv[arg_idx++];
    }

    // determine the TX port
    const char* tx_port = "queue-1";
    if (arg_idx < argc) {
        tx_port = argv[arg_idx++];
    }

    int iterations = 10000000;
    if (arg_idx < argc) {
        const char* arg = argv[arg_idx++];
        if (strcmp(arg, "-") != 0) {
            iterations = atoi(arg);
        }
    }

    SBRX rx;
    SBTX tx;
    rx.init(rx_port);
    tx.init(tx_port);

    int count = 0;
    sb_packet p = {0};

    if (is_first) {
        // start measuring time taken
        std::chrono::steady_clock::time_point start_time = std::chrono::steady_clock::now();

        while (count < iterations) {
            // busy-loop for minimum latency
            while (!tx.send(p))
                ;
            while (!rx.recv(p))
                ;

            for (int i = 0; i < 8; i++) {
                (*((uint32_t*)(&p.data[4 * i])))++;
            }

            count++;
        }

        // print output to make sure it is not optimized away
        printf("Output: {");
        for (int i = 0; i < 8; i++) {
            // print next entry
            uint32_t out = *((uint32_t*)(&p.data[4 * i]));
            printf("%0d", out);
            if (i != 7) {
                printf(", ");
            }

            // check entry
            if (out != (2 * iterations)) {
                throw std::runtime_error("MISMATCH");
            }
        }
        printf("}\n");

        // stop measuring time taken
        std::chrono::steady_clock::time_point stop_time = std::chrono::steady_clock::now();
        double t =
            1.0e-6 *
            (std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());

        printf("Latency: ");
        double latency = t / (1.0 * iterations);
        if (latency < 1e-6) {
            printf("%0.1f ns", latency * 1.0e9);
        } else if (latency < 1e-3) {
            printf("%0.1f us", latency * 1.0e6);
        } else if (latency < 1) {
            printf("%0.1f ms", latency * 1.0e3);
        } else {
            printf("%0.1f s", latency);
        }
        printf("\n");
    } else {
        while (count < iterations) {
            // busy-loop for minimum latency
            while (!rx.recv(p))
                ;

            for (int i = 0; i < 8; i++) {
                (*((uint32_t*)(&p.data[4 * i])))++;
            }

            // busy-loop for minimum latency
            while (!tx.send(p))
                ;

            count++;
        }
    }

    return 0;
}
