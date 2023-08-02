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
    const char* rx_arg = "5555";
    if (arg_idx < argc) {
        rx_arg = argv[arg_idx++];
    }
    char rx_port[128];
    sprintf(rx_port, "queue-%s", rx_arg);

    // determine the TX port
    const char* tx_arg = "5555";
    if (arg_idx < argc) {
        tx_arg = argv[arg_idx++];
    }
    char tx_port[128];
    sprintf(tx_port, "queue-%s", tx_arg);

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
                // TODO: clean this up...
                (*((uint32_t*)(&p.data[4 * i])))++;
            }

            count++;
        }

        // print output to make sure it is not optimized away
        printf("Output: {");
        for (int i = 0; i < 8; i++) {
            // TODO: clean this up...
            printf("%0d", *((uint32_t*)(&p.data[4 * i])));
            if (i != 7) {
                printf(", ");
            }
        }
        printf("}\n");

        // stop measuring time taken
        std::chrono::steady_clock::time_point stop_time = std::chrono::steady_clock::now();
        double t =
            1.0e-6 *
            (std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());

        double latency = t / (1.0 * iterations);
        printf("Latency: %0.1f ns\n", latency * 1.0e9);
    } else {
        while (count < iterations) {
            // busy-loop for minimum latency
            while (!rx.recv(p))
                ;

            for (int i = 0; i < 8; i++) {
                // TODO: clean this up...
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
