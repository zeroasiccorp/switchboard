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

void dut_send(const uint32_t data, const uint32_t addr){
    // format the packet
    umi_packet p = {0};
    umi_pack(p, data, addr);

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

int main(int argc, char* argv[]) {
    // process command-line arguments

    int rx_port = 5556;
    if (argc >= 2) {
        rx_port = atoi(argv[1]);
    }

    int tx_port = 5555;
    if (argc >= 3) {
        tx_port = atoi(argv[2]);
    }

    const char* binfile = "riscv/hello.bin";
    if (argc >= 4) {
        binfile = argv[3];
    }    

    // set up UMI ports
    init(rx_port, tx_port);

    // start measuring time taken here
    std::chrono::steady_clock::time_point start_time = std::chrono::steady_clock::now();

    // put the DUT into reset
    dut_send(0, 0x20000000);

    // write program
    std::ifstream file(binfile, std::ios::in|std::ios::binary);
    uint32_t waddr = 0;
    do {
        // read into the buffer
        uint32_t data = 0;
        file.read((char*)&data, 4);

        // write value
        dut_send(data, waddr);

        // increment address
        waddr += 4;
    } while(file);

    // take DUT out of reset
    dut_send(1, 0x20000000);

    // receive characters sent by DUT
    uint16_t exit_code;
    uint32_t data, addr;
    while(1){
        dut_recv(data, addr);
        if (addr == 0x10000000) {
            printf("%c", data & 0xff);
            fflush(stdout);
        } else if (addr == 0x10000008) {
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