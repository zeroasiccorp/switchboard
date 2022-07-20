#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sched.h>
#include <sys/time.h>

#include "vpidpi/umi_intf.h"

struct timeval stop_time, start_time;
spsc_queue* rxq;
spsc_queue* txq;
uint32_t rxp[8] = {0};
uint32_t txp[8] = {0};

void my_umi_init(int rx_port, int tx_port, int mode) {
    // determine URIs
    char rx_uri[128];
    char tx_uri[128];
    if (mode == UMI_QUEUE) {
        sprintf(rx_uri, "/tmp/feeds-%d", rx_port);
        sprintf(tx_uri, "/tmp/feeds-%d", tx_port);
    } else if (mode == UMI_TCP) {
        sprintf(rx_uri, "127.0.0.1:%d", rx_port);
        sprintf(tx_uri, "127.0.0.1:%d", tx_port);
    } else {
        fprintf(stderr, "Unknown interface mode.\n");
        exit(1);
    }

    rxq = umi_init(rx_uri, false, (umi_mode)mode);
    txq = umi_init(tx_uri, true, (umi_mode)mode);
}

void my_umi_recv() {
    while (spsc_recv(rxq, (uint8_t*)rxp, 32) == 0){
        sched_yield();
    }
}

void my_umi_send() {
    while (spsc_send(txq, (uint8_t*)txp, 32) == 0) {
        sched_yield();
    }
}

void dut_send(const uint32_t data, const uint32_t addr){
    txp[1] = addr;
    txp[3] = data;
    my_umi_send();
}

void dut_recv(uint32_t* data, uint32_t* addr){
    my_umi_recv();
    *addr = rxp[1];
    *data = rxp[3];
}

int main(int argc, char* argv[]) {
    int rx_port = 5556;
    int tx_port = 5555;
    int intf_mode = 0;
    const char* binfile = "build/sw/hello.bin";
    if (argc >= 2) {
        rx_port = atoi(argv[1]);
    }
    if (argc >= 3) {
        tx_port = atoi(argv[2]);
    }
    if (argc >= 4) {
        intf_mode = atoi(argv[3]);
    }
    if (argc >= 5) {
        binfile = argv[4];
    }    

    my_umi_init(rx_port, tx_port, intf_mode);

    gettimeofday(&start_time, NULL);

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
    while(1){
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

    gettimeofday(&stop_time, NULL);

    unsigned long t_us = 0;
    t_us += ((stop_time.tv_sec - start_time.tv_sec) * 1000000);
    t_us += (stop_time.tv_usec - start_time.tv_usec);
    double t = 1.0e-6*t_us;

    printf("Time taken: %0.3f ms\n", t*1.0e3);

    return exit_code;
}