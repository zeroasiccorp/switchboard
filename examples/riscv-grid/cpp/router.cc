#include <vector>
#include <iostream>
#include <thread>
#include <cstdlib>

#include "phiber.hpp"

// connections to each of the entries in the grid
UmiConnection** rx_connections;
UmiConnection** tx_connections;

int rows;
int cols;

void cleanup() {
    for (int i=0; i<rows; i++) {
        delete rx_connections[i];
        delete tx_connections[i];
    }

    delete rx_connections;
    delete tx_connections;
}

void init(int argc, char* argv[]) {
    // determine number of rows and columns

    int arg_idx = 1;

    if (arg_idx < argc) {
        rows = atoi(argv[arg_idx++]);
    }
    if (arg_idx < argc) {
        cols = atoi(argv[arg_idx++]);
    }

    // create arrays of connections, and register a cleanup function
    rx_connections = new UmiConnection*[rows];
    tx_connections = new UmiConnection*[rows];
    for (int i=0; i<rows; i++) {
        rx_connections[i] = new UmiConnection[cols];
        tx_connections[i] = new UmiConnection[cols];
    }
    std::atexit(cleanup);

    // deal with rx connections
    for (int i=0; i<rows; i++) {
        for (int j=0; j<cols; j++) {
            // add RX connection
            if (arg_idx < argc) {
                int port = atoi(argv[arg_idx++]);
                if (port > 0) {
                    char uri[128];
                    sprintf(uri, "queue-%d", port);
                    rx_connections[i][j].init(uri, false, false);
                }
            }

            // add TX connection
            if (arg_idx < argc) {
                int port = atoi(argv[arg_idx++]);
                if (port > 0) {
                    char uri[128];
                    sprintf(uri, "queue-%d", port);
                    tx_connections[i][j].init(uri, true, false);
                }
            }
        }
    }
}

int main(int argc, char* argv[]) {
    // set up connections
    init(argc, argv);

    int i, j;
    umi_packet p;
    uint32_t packet_row, packet_col;
    while (true) {
        // loop over the connections
        for (i=0; i<rows; i++) {
            for (j=0; j<cols; j++) {
                if (rx_connections[i][j].is_active()) {
                    // if this connection is active, try to receive a packet
                    if (rx_connections[i][j].recv_peek(p)) {
                        // determine where the packet is headed
                        packet_row = (p[7] >> 24) & 0xff;
                        packet_col = (p[7] >> 16) & 0xff;

                        // make sure the destination exists and is active
                        assert(
                            (0 <= packet_row) && (packet_row < rows) &&
                            (0 <= packet_col) && (packet_col < cols) &&
                            tx_connections[packet_row][packet_col].is_active()
                        );

                        // try to send the packet, removing it from
                        // the RX queue if the send is successful
                        if(tx_connections[packet_row][packet_col].send(p)) {
                            rx_connections[i][j].recv();
                        }
                    }
                }
            }
        }
    }

    return 0;
}