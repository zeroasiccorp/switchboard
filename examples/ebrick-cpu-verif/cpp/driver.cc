#include <chrono>
#include <thread>
#include <fstream>
#include <unistd.h>
#include <signal.h>

#include "switchboard.hpp"
#include "umilib.hpp"

SBRX rx1, rx_tb;
SBTX tx1, tx_tb;

uint32_t sram[32768] = {0};

void init() {
    // clear old queues
    delete_shared_queue("queue-5555");
    delete_shared_queue("queue-5556");
    delete_shared_queue("queue-5557");
    delete_shared_queue("queue-5558");

    // initialize queues
    tx1.init("queue-5555");
    rx1.init("queue-5556");
    tx_tb.init("queue-5557");
    rx_tb.init("queue-5558");
}

bool gpio_write(const uint32_t data) {
    // form the UMI packet
    sb_packet p;
    umi_pack((uint32_t*)p.data, UMI_WRITE_NORMAL, 2, 0, 0, 0, (uint8_t*)(&data), 4);

    // send the packet
    return tx_tb.send(p);
}

void init_sram(const char* binfile) {
    FILE* f;
    f = fopen(binfile, "rb");
    fread(sram, sizeof(uint32_t), sizeof(sram), f);
}

void start_simulator_process(const char* simulator) {
    execl(simulator, simulator, (char*)NULL);
}

int main(int argc, char* argv[]) {
    // process command-line arguments

    int arg_idx = 1;

    const char* simulator = "verilator/obj_dir/Vtestbench";
    if (arg_idx < argc) {
        simulator = argv[arg_idx++];
    }

    const char* binfile = "riscv/hello.bin";
    if (arg_idx < argc) {
        binfile = argv[arg_idx++];
    }

    // set up UMI ports (important to do this before forking, since this
    // initializes the shared memory queues)
    init();

    // start the simulator as a child process
    int pid = fork();
    if (pid == 0) {
        start_simulator_process(simulator);
    }

    // initialize SRAM model
    init_sram(binfile);

    // put chiplet in reset
    while(!gpio_write(0));

    // release chiplet from reset
    while(!gpio_write(1));

    // handle UMI packets

    int exit_code;

    while (1) {
        // try to receive a packet
        sb_packet p;
        if(rx1.recv_peek(p)) {
            // parse the packet
            uint32_t opcode, size, user;
            uint64_t dstaddr, srcaddr;
            uint32_t data_arr[4];
            umi_unpack((uint32_t*)p.data, opcode, size, user,
                dstaddr, srcaddr, (uint8_t*)data_arr, 16);

            // handle the packet
            if (opcode == UMI_WRITE_NORMAL) {
                // ACK
                rx1.recv();

                // implement the write
                if (dstaddr == 0x500000) {
                    printf("%c", data_arr[0] & 0xff);
                    fflush(stdout);
                } else if (dstaddr == 0x600000) {
                    uint16_t kind = data_arr[0] & 0xffff;
                    if (kind == 0x3333) {
                        exit_code = (data_arr[0] >> 16) & 0xffff;
                        break;
                    } else if (kind == 0x5555) {
                        exit_code = 0;
                        break;
                    }
                } else {
                    sram[dstaddr>>2] = data_arr[0];
                }
            } else if (opcode == UMI_READ) {
                // try to send a read response
                sb_packet resp;
                umi_pack((uint32_t*)resp.data, UMI_WRITE_RESPONSE, 2, 0, srcaddr, 0,
                    (uint8_t*)(&sram[dstaddr>>2]), 4);
                if (tx1.send(resp)) {
                    // ACK if the response was sent successfully
                    rx1.recv();
                }
            }
        }
    }

    // stop the simulator process
    kill(pid, SIGINT);
    wait(NULL);

    return exit_code;
}
