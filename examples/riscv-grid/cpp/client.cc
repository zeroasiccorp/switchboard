#include <chrono>
#include <thread>
#include <fstream>

#include "umiverse.hpp"

UmiConnection rx;
UmiConnection tx;

void init(int rx_port, int tx_port) {
    // RX
    char rx_uri[128];
    sprintf(rx_uri, "queue-%d", rx_port);
    rx.init(rx_uri, false, false);

    // TX
    char tx_uri[128];
    sprintf(tx_uri, "queue-%d", tx_port);
    tx.init(tx_uri, true, false);
}

void dut_send(const uint32_t data, const uint32_t addr, const uint32_t row, const uint32_t col){
    // format the packet
    umi_packet p = {0};
    umi_pack(p, data, addr);

    // add row/col information
    // TODO: cleanup
    p[7] = 0;
    p[7] |= (row & 0xf) << 24;
    p[7] |= (col & 0xf) << 16;

    // send the packet
    while (!tx.send(p)) {
        std::this_thread::yield();
    }
}

void dut_recv(uint32_t& data, uint32_t& addr){
    // receive packet
    umi_packet p;
    while (!rx.recv(p)){
        std::this_thread::yield();
    }

    // parse packet
    umi_unpack(p, data, addr);
}

void init_chip(int row, int col, int rows, int cols, const char* binfile) {
    // write program
    std::ifstream file(binfile, std::ios::in|std::ios::binary);
    uint32_t waddr = 0;
    do {
        // read into the buffer
        uint32_t data = 0;
        file.read((char*)&data, 4);

        // write value
        dut_send(data, waddr, row, col);

        // increment address
        waddr += 4;
    } while(file);

    // write chiplet index and rows/cols
    uint32_t memory_size = 1 << 17;
    dut_send(row,  memory_size - 4,  row, col);
    dut_send(col,  memory_size - 8,  row, col);
    dut_send(rows, memory_size - 12, row, col);
    dut_send(cols, memory_size - 16, row, col);
    dut_send(0, memory_size - 20, row, col); // clear for CPU-CPU communication
}

int main(int argc, char* argv[]) {
    // process command-line arguments

    int rows = 1;
    if (argc >= 2) {
        rows = atoi(argv[1]);
    }

    int cols = 1;
    if (argc >= 3) {
        cols = atoi(argv[2]);
    }

    int rx_port = 5556;
    if (argc >= 4) {
        rx_port = atoi(argv[3]);
    }

    int tx_port = 5555;
    if (argc >= 5) {
        tx_port = atoi(argv[4]);
    }

    const char* binfile = "riscv/hello.bin";
    if (argc >= 6) {
        binfile = argv[5];
    }    

    // set up UMI ports
    init(rx_port, tx_port);

    // start measuring time taken here
    std::chrono::steady_clock::time_point start_time = std::chrono::steady_clock::now();

    // put all chips in reset
    for (int row=0; row<rows; row++) {
        for (int col=0; col<cols; col++) {
            if ((row == 0) && (col == 0)) {
                // skip since this is where the client resides
                continue;
            } else {
                dut_send(0, 0x400000, row, col);
            }
        }
    }

    // program all chips
    // it's important to not release any chips from reset until
    // all chip have been programmed, since some might write to
    // the memory of other chips, and those writes may be clobbered
    // by the programming operation.
    for (int row=0; row<rows; row++) {
        for (int col=0; col<cols; col++) {
            if ((row == 0) && (col == 0)) {
                // skip since this is where the client resides
                continue;
            } else {
                init_chip(row, col, rows, cols, binfile);
            }
        }
    }

    // 17 ms seems to be the smallest wait that is OK
    // TODO: use feedback to determine when it is OK
    // to proceed
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // release all chips from reset
    for (int row=0; row<rows; row++) {
        for (int col=0; col<cols; col++) {
            if ((row == 0) && (col == 0)) {
                // skip since this is where the client resides
                continue;
            } else {
                dut_send(1, 0x400000, row, col);
            }
        }
    }

    // receive characters sent by DUT
    uint16_t exit_code;
    uint32_t data, addr;
    while(1){
        dut_recv(data, addr);
        if (addr == 0x500000) {
            printf("%c", data & 0xff);
            fflush(stdout);
        } else if (addr == 0x600000) {
            uint16_t kind = data & 0xffff;
            if (kind == 0x3333) {
                exit_code = (data >> 16) & 0xffff;
                break;
            } else if (kind == 0x5555) {
                exit_code = 0;
                break;
            }
        }
    }

    // determine how long the process took
    std::chrono::steady_clock::time_point stop_time = std::chrono::steady_clock::now();
    double t = 1.0e-6*(std::chrono::duration_cast<std::chrono::microseconds>(stop_time - start_time).count());

    // print out the runtime
    printf("Time taken: %0.3f ms\n", t*1e3);

    return exit_code;
}