#include <iostream>
#include <thread>

#include "umiverse.hpp"

// hub
UmiConnection connections[10];

uint32_t router_row = 0;
uint32_t router_col = 0;

typedef enum routes {
    h_rx=0,
    h_tx=1,
    n_rx=2,
    n_tx=3,
    e_rx=4,
    e_tx=5,
    s_rx=6,
    s_tx=7,
    w_rx=8,
    w_tx=9
} routes;

void init(int argc, char* argv[]) {
    // deal with row/col

    if (argc >= 2) {
        router_row = atoi(argv[1]);
    }
    if (argc >= 3) {
        router_col = atoi(argv[2]);
    }

    // deal with other connections
    int conn_idx = 0;
    bool conn_is_tx = false;
    for (int i=3; i<argc; i++){
        int port = atoi(argv[i]);

        if (port > 0) {  // zero value means the port is unused
            char uri[128];
            sprintf(uri, "queue-%d", port);
            connections[conn_idx].init(uri, conn_is_tx, false);
        }

        // move onto next connection
        conn_idx++;
        conn_is_tx = !conn_is_tx;
    }
}

int main(int argc, char* argv[]) {
    // set up connections
    init(argc, argv);
    
    // handle incoming packets
    while (true) {
        // round robin over the RX ports
        bool any_recv = false;

        for (int i=0; i<10; i+=2) {
            if (connections[i].is_active()) {
                umi_packet p;
                if (connections[i].recv(p)) {
                    any_recv = true;

                    // extract row / column
                    uint32_t packet_row = (p[7] >> 24) & 0xff;
                    uint32_t packet_col = (p[7] >> 16) & 0xff;

                    // routing order: north, south, east, west, hub
                    UmiConnection* destination = NULL;
                    if (packet_row < router_row){
                        // route to north
                        destination = &connections[n_tx];
                    } else if (packet_row > router_row) {
                        // route to south
                        destination = &connections[s_tx];
                    } else if (packet_col > router_col) {
                        // route to east
                        destination = &connections[e_tx];
                    } else if (packet_col < router_col) {
                        // route to west
                        destination = &connections[w_tx];
                    } else {
                        // route into hub, clearing the row/col address information
                        p[7] &= 0xffff;
                        destination = &connections[h_tx];
                    }

                    // block until we can send the packet to the right place
                    // TODO: is there a deadlock risk here?
                    while(!destination->send(p)) {
                        std::this_thread::yield();
                    }
                }
            }
        }

        if (!any_recv) {
            std::this_thread::yield();
        }
    }

    return 0;
}