#include <chrono>
#include <memory>
#include <mutex>

#include "switchboard.hpp"
#include "svdpi.h"

// function definitions
#ifdef __cplusplus
extern "C" {
#endif
    extern void pi_umi_init(int* id, const char* uri, int is_tx);
    extern void pi_umi_recv(int id, svBitVecVal* rbuf, int* success);
    extern void pi_umi_send(int id, const svBitVecVal* sbuf, int* success);
    extern void pi_time_taken(double* t);
#ifdef __cplusplus
}
#endif

static std::vector<std::unique_ptr<UmiConnection>> connections;

void pi_umi_init(int* id, const char* uri, int is_tx) {
    // create a new connection
    connections.push_back(std::unique_ptr<UmiConnection>(new UmiConnection()));

    // initialize the connection
    connections.back()->init(uri, is_tx, false);

    // assign the ID of this connection
    *id = connections.size() - 1;
}

void pi_umi_recv(int id, svBitVecVal* rbuf, int* success) {
    umi_packet p;
    
    if (connections[id]->recv(p)) {
        memcpy(rbuf, &p, 32);  // TODO: possible to remove this?
        *success = 1;
    } else {
        *success = 0;
    } 
}

void pi_umi_send(int id, const svBitVecVal* sbuf, int* success) {
    umi_packet p;
    memcpy(&p, sbuf, 32);  // TODO: possible to remove this?
    
    if (connections[id]->send(p)) {
        *success = 1;
    } else {
        *success = 0;
    }
}

void pi_time_taken(double* t) {
    static std::chrono::steady_clock::time_point start_time;
    static std::chrono::steady_clock::time_point stop_time;

    // compute time taken in seconds
	stop_time = std::chrono::steady_clock::now();
    *t = 1.0e-6*(std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());
    start_time = std::chrono::steady_clock::now();
}
