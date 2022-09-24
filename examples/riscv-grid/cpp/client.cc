#include <chrono>
#include <thread>
#include <fstream>

#include "switchboard.hpp"
#include "umilib.hpp"

SBRX rx;
SBTX tx;

// don't have this defined in multiple places
#define PICORV32_MEM_TOP (1<<17)

void init(int rx_port, int tx_port) {
    // RX
    char rx_uri[128];
    sprintf(rx_uri, "queue-%d", rx_port);
    rx.init(rx_uri);

    // TX
    char tx_uri[128];
    sprintf(tx_uri, "queue-%d", tx_port);
    tx.init(tx_uri);
}

void dut_send(const uint32_t data, const uint32_t addr, const uint32_t row, const uint32_t col){
    // determine destination address
    uint64_t dstaddr;
    dstaddr = 0;
    dstaddr |= ((row & 0xf) << 24);
    dstaddr |= ((col & 0xf) << 16);
    dstaddr <<= 32;
    dstaddr |= addr;

    // form the UMI packet
    sb_packet p;
    umi_pack((uint32_t*)p.data, UMI_WRITE_NORMAL, dstaddr, 0, data);
    p.destination = ((row & 0xf) << 8) | (col & 0xf);
    p.last = 1;

    // send the packet
    tx.send_blocking(p);
}

void dut_recv(uint32_t& data, uint32_t& addr){
    // receive packet
    sb_packet p;
    rx.recv_blocking(p);

    // parse packet
    uint32_t opcode, size, user;
    uint64_t dstaddr, srcaddr;
    uint32_t data_arr[4];
    umi_unpack((uint32_t*)p.data, opcode, size, user, dstaddr, srcaddr, data_arr);

    // only the lowest 32 bits of data and address are used
    data = data_arr[0];
    addr = dstaddr & 0xffffffff;
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

    // write to a certain region of memory to specify the row, col
    // address of the chip, and the total number of rows and columns
    dut_send(row,  (uint32_t)(PICORV32_MEM_TOP) -  4, row, col);
    dut_send(col,  (uint32_t)(PICORV32_MEM_TOP) -  8, row, col);
    dut_send(rows, (uint32_t)(PICORV32_MEM_TOP) - 12, row, col);
    dut_send(cols, (uint32_t)(PICORV32_MEM_TOP) - 16, row, col);
}

int main(int argc, char* argv[]) {
    // process command-line arguments

    int arg_idx = 1;

    int rows = 1;
    if (arg_idx < argc) {
        rows = atoi(argv[arg_idx++]);
    }

    int cols = 1;
    if (arg_idx < argc) {
        cols = atoi(argv[arg_idx++]);
    }

    int rx_port = 5556;
    if (arg_idx < argc) {
        rx_port = atoi(argv[arg_idx++]);
    }

    int tx_port = 5555;
    if (arg_idx < argc) {
        tx_port = atoi(argv[arg_idx++]);
    }

    const char* binfile = "riscv/hello.bin";
    if (arg_idx < argc) {
        binfile = argv[arg_idx++];
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

    // write command-line provided parameters into the top of memory
    // TODO: don't hard-code the memory size
    int param_idx = 4;  // the first 4 are already populated
    while (arg_idx < argc) {
        int param_val = atoi(argv[arg_idx++]);
        for (int row=0; row<rows; row++) {
            for (int col=0; col<cols; col++) {
                if ((row == 0) && (col == 0)) {
                    // skip since this is where the client resides
                    continue;
                } else {
                    dut_send(param_val, PICORV32_MEM_TOP - 4*(param_idx+1), row, col);
                }
            }
        }
        param_idx++;
    }

    // we need to wait for all of the messages from the client to have been
    // accepted by the router, since this means they have at least been
    // queued up for writing to the memory of each CPU.  we can then safely
    // release the reset for all processors, since any inter-CPU writes
    // will be queued up afterwards
    while (!tx.all_read()) {
        std::this_thread::yield();
    }

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
