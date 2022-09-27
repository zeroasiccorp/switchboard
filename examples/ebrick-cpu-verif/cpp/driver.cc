#include <chrono>
#include <thread>
#include <fstream>

#include "switchboard.hpp"

UmiConnection rx1, rx_tb;
UmiConnection tx1, tx_tb;

uint32_t sram[32768] = {0};

void init() {
    // clear old queues
    delete_shared_queue("queue-5555");
    delete_shared_queue("queue-5556");
    delete_shared_queue("queue-5557");
    delete_shared_queue("queue-5558");

    // initialize queues
    tx1.init("queue-5555", true, false);
    rx1.init("queue-5556", false, false);
    tx_tb.init("queue-5557", true, false);
    rx_tb.init("queue-5558", false, false);
}

bool gpio_write(const uint32_t data) {
    // form the UMI packet
    umi_packet p;
    umi_pack(p, UMI_WRITE_NORMAL, 0, 0, data);

    // send the packet
    return tx_tb.send(p);
}

void init_sram(const char* binfile) {
    FILE* f;
    f = fopen(binfile, "rb");
    fread(sram, sizeof(uint32_t), sizeof(sram), f);
}

int main(int argc, char* argv[]) {
    // process command-line arguments

    int arg_idx = 1;

    const char* binfile = "riscv/hello.bin";
    if (arg_idx < argc) {
        binfile = argv[arg_idx++];
    }

    // set up UMI ports
    init();

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
        umi_packet p;
        if(rx1.recv_peek(p)) {
            // parse the packet
            uint32_t opcode, size, user;
            uint64_t dstaddr, srcaddr;
            uint32_t data_arr[4];
            umi_unpack(p, opcode, size, user, dstaddr, srcaddr, data_arr);

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
                umi_packet resp;
                umi_pack(resp, UMI_WRITE_NORMAL, srcaddr, 0, sram[dstaddr>>2]);
                if (tx1.send(resp)) {
                    // ACK if the response was sent successfully
                    rx1.recv();
                }
            }
        }
    }

    return exit_code;
}
