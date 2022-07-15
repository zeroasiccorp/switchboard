#include "vpidpi/spsc_queue.hpp"
#include <stdio.h>
#include <thread>

struct timeval stop_time, start_time;

static bip::managed_shared_memory rxs;
static bip::managed_shared_memory txs;

ring_buffer* rxq;
ring_buffer* txq;

packet rxp;
packet txp;

void umi_init(int rx_port, int tx_port) {
    // determine RX URI
    char rx_uri[128];
    sprintf(rx_uri, "shmem-%d", rx_port);
    rxq = spsc_open(rxs, rx_uri);

    // determine TX URI
    char tx_uri[128];
    sprintf(tx_uri, "shmem-%d", tx_port);
    txq = spsc_open(txs, tx_uri);
    txq->reset();
}

void umi_recv() {
    while (!rxq->pop(rxp)){
        std::this_thread::yield();
    }
}

void umi_send() {
    while (!txq->push(txp)) {
        std::this_thread::yield();
    }
}

void dut_send(const uint32_t data, const uint32_t addr){
    txp[0] = 0;
    txp[1] = addr;
    txp[2] = 0;
    txp[3] = data;
    txp[4] = 0;
    txp[5] = 0;
    txp[6] = 0;
    txp[7] = 0;
    umi_send();
}

void dut_recv(uint32_t* data, uint32_t* addr){
    umi_recv();
    *addr = rxp[1];
    *data = rxp[3];
}

int main(int argc, char* argv[]) {
    int rx_port = 5556;
    int tx_port = 5555;
    const char* binfile = "build/sw/hello.bin";
    if (argc >= 2) {
        rx_port = atoi(argv[1]);
    }
    if (argc >= 3) {
        tx_port = atoi(argv[2]);
    }
    if (argc >= 4) {
        binfile = argv[3];
    }
    
    umi_init(rx_port, tx_port);
    dut_send(0, 0x20000000);

    FILE *ptr;
    ptr = fopen(binfile, "rb");
    uint8_t buf[4];
    int nread;
    uint32_t waddr = 0;
    while ((nread = fread(buf, 1, 4, ptr)) > 0){
        // fill in extra values with zeros
        for (int i=nread; i<sizeof(buf); i++){
            buf[i] = 0;
        }

        // format as an integer
        uint32_t outgoing = 0;
        outgoing |= (buf[0] <<  0);
        outgoing |= (buf[1] <<  8);
        outgoing |= (buf[2] << 16);
        outgoing |= (buf[3] << 24);

        // write value
        dut_send(outgoing, waddr);

        waddr += 4;
    }
    dut_send(1, 0x20000000);
    uint16_t exit_code;
    uint32_t data, addr;
    while(true){
        dut_recv(&data, &addr);
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
    return exit_code;
}