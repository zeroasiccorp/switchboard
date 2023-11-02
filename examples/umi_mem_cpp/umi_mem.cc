// Fast software model large memory (2 GB), useful for booting Linux
// Copyright (C) 2023 Zero ASIC

#include <cinttypes>
#include <stdexcept>

#include "switchboard.hpp"
#include "umilib.h"
#include "umilib.hpp"

SBTX tx;
SBRX rx;

SBTX req_tx;
SBRX rep_rx;

#define SRAM_BASE 0x0

#define SRAM_BASE_SIZE (1UL << 31) // 2 GB
#define MAX_FLIT_BYTES 32

uint8_t* sram;

uint8_t zeros[MAX_FLIT_BYTES] = {0};

bool in_range(uint64_t addr, size_t bytes, uint64_t base, size_t extent) {
    return (base <= addr) && (bytes <= extent) && ((addr - base) <= (extent - bytes));
}

void init(std::string tx_uri, std::string rx_uri, std::string req_tx_uri, std::string rep_rx_uri) {
    // initialize queues
    tx.init(tx_uri);
    rx.init(rx_uri);
    req_tx.init(req_tx_uri);
    rep_rx.init(rep_rx_uri);
}

int64_t atomic_op(uint64_t dstaddr, uint8_t data_arr[], uint32_t opcode, uint32_t size) {
    // determine whether this transaction is in cached or uncached memory
    uint8_t* mem;
    uint64_t offset;
    if (in_range(dstaddr, 1 << size, SRAM_BASE, SRAM_BASE_SIZE)) {
        mem = sram;
        offset = dstaddr - SRAM_BASE;
    } else {
        fprintf(stderr, "***ERROR: dstaddr for atomic_op out of range (0x%" PRIx64 ").\n", dstaddr);
        return 0;
    }

    // format operands as a 64-bit signed integers
    // the integer is signed so that shorter types
    // will sign extend, which is needed for MAX and MIN
    // (for other operations, whether or not there is
    // sign-extension has no effect)
    int64_t memval, datval;
    uint64_t memvalu, datvalu;
    if (size == 0) {
        memval = *((int8_t*)(mem + offset));
        datval = *((int8_t*)(data_arr));
        memvalu = *((uint8_t*)(mem + offset));
        datvalu = *((uint8_t*)(data_arr));
    } else if (size == 1) {
        memval = *((int16_t*)(mem + offset));
        datval = *((int16_t*)(data_arr));
        memvalu = *((uint16_t*)(mem + offset));
        datvalu = *((uint16_t*)(data_arr));
    } else if (size == 2) {
        memval = *((int32_t*)(mem + offset));
        datval = *((int32_t*)(data_arr));
        memvalu = *((uint32_t*)(mem + offset));
        datvalu = *((uint32_t*)(data_arr));
    } else if (size == 3) {
        memval = *((int64_t*)(mem + offset));
        datval = *((int64_t*)(data_arr));
        memvalu = *((uint64_t*)(mem + offset));
        datvalu = *((uint64_t*)(data_arr));
    } else {
        fprintf(stderr, "***ERROR: size=%u is not supported for atomic operations\n", size);
        return 0;
    }

    // perform operation
    int64_t y;
    uint64_t u;
    bool sign = true;
    if (opcode == UMI_REQ_ATOMICSWAP) {
        y = datval;
    } else if (opcode == UMI_REQ_ATOMICADD) {
        y = memval + datval;
    } else if (opcode == UMI_REQ_ATOMICAND) {
        y = memval & datval;
    } else if (opcode == UMI_REQ_ATOMICOR) {
        y = memval | datval;
    } else if (opcode == UMI_REQ_ATOMICXOR) {
        y = memval ^ datval;
    } else if (opcode == UMI_REQ_ATOMICMIN) {
        y = (memval <= datval) ? memval : datval;
    } else if (opcode == UMI_REQ_ATOMICMAX) {
        y = (memval >= datval) ? memval : datval;
    } else if (opcode == UMI_REQ_ATOMICMINU) {
        sign = false;
        u = (memvalu <= datvalu) ? memvalu : datvalu;
    } else if (opcode == UMI_REQ_ATOMICMAXU) {
        sign = false;
        u = (memvalu >= datvalu) ? memvalu : datvalu;
    } else {
        fprintf(stderr, "***ERROR: opcode=0x%02x is not a valid atomic operation\n", opcode);
    }

    // store result to memory address
    // send old value back as a response
    if (sign) {
        memcpy(mem + offset, &y, 1 << size);
        return memval;
    } else {
        memcpy(mem + offset, &u, 1 << size);
        return memvalu;
    }
}

class response_state {
  public:
    bool in_progress;
    uint32_t read_bytes_remaining;
    uint64_t read_dstaddr;
    uint32_t read_size;
    uint32_t flit_bytes;

    SBTX* out_channel;

    response_state() : in_progress(false), read_bytes_remaining(0) {}

    void done(umi_packet* utxp) {
        if (read_bytes_remaining) {
            read_bytes_remaining -= flit_bytes;
            utxp->srcaddr += flit_bytes;
            utxp->dstaddr += flit_bytes;
            read_dstaddr += flit_bytes;
        }
        in_progress = false;
    }
} resp;

int main(int argc, char* argv[]) {
    // process command-line arguments

    int arg_idx = 1;

    sram = new uint8_t[SRAM_BASE_SIZE];
    if (!sram) {
        // have to error out at this point, since we can't
        // model a memory without, well, memory...
        throw std::runtime_error("Unable to allocate memory!");
    }

    std::string req_rx_uri = "mem-req-rx.q";
    std::string rep_tx_uri = "mem-rep-tx.q";

    std::string req_tx_uri = "mem-req-tx.q";
    std::string rep_rx_uri = "mem-rep-rx.q";

    while (arg_idx < argc) {
        char* s = argv[arg_idx++];
        if (strcmp(s, "--rep-tx") == 0) {
            if (arg_idx < argc) {
                rep_tx_uri = std::string(argv[arg_idx++]);
            }
        } else if (strcmp(s, "--req-rx") == 0) {
            if (arg_idx < argc) {
                req_rx_uri = std::string(argv[arg_idx++]);
            }
        } else if (strcmp(s, "--req-tx") == 0) {
            if (arg_idx < argc) {
                req_tx_uri = std::string(argv[arg_idx++]);
            }
        } else if (strcmp(s, "--rep-rx") == 0) {
            if (arg_idx < argc) {
                rep_rx_uri = std::string(argv[arg_idx++]);
            }
        } else {
            fprintf(stderr, "***ERROR: invalid argument, ignoring...\n");
        }
    }

    // set up UMI ports

    init(rep_tx_uri, req_rx_uri, req_tx_uri, rep_rx_uri);

    // response packet

    sb_packet txp;
    umi_packet* utxp = (umi_packet*)txp.data;

    // response state
    response_state resp;

    while (1) {
        // try to receive a packet

        sb_packet rxp;

        if (rx.recv_peek(rxp)) {
            // interpret the received SB packet as a UMI packet
            umi_packet* urxp = (umi_packet*)rxp.data;

            // remove the upper bits with row/col address
            uint64_t dstaddr = urxp->dstaddr & 0xffffffffff;

            // extract important fields from the command
            uint32_t opcode = umi_opcode(urxp->cmd);
            uint32_t size = umi_size(urxp->cmd);
            uint32_t len = umi_len(urxp->cmd);

            // calculate the number of bytes in this transaction
            uint32_t nbytes;
            if (opcode == UMI_REQ_ATOMIC) {
                // atomic transaction implies LEN=0
                nbytes = 1 << size;
            } else {
                nbytes = (len + 1) << size;
            }

            // interpret the packet contents
            if ((opcode == UMI_REQ_POSTED) || ((opcode == UMI_REQ_WRITE) && (!resp.in_progress))) {
                // ACK
                rx.recv();

                if (!in_range(dstaddr, nbytes, SRAM_BASE, SRAM_BASE_SIZE)) {
                    fprintf(stderr,
                        "***ERROR: Memory write out of range: dstaddr=0x%" PRIx64
                        ", flit_bytes=%u\n",
                        dstaddr, nbytes);
                } else if (nbytes > sizeof(urxp->data)) {
                    fprintf(stderr,
                        "***ERROR: Number of bytes in write transaction (%ud)"
                        " exceeds the data bus width (%zu).\n",
                        nbytes, sizeof(urxp->data));
                } else {
                    memcpy(&sram[dstaddr - SRAM_BASE], urxp->data, nbytes);
                }

                // send a response if necessary
                if (opcode == UMI_REQ_WRITE) {
                    // format the response
                    utxp->cmd = umi_pack(UMI_RESP_WRITE, 0, size, len, umi_eom(urxp->cmd),
                        umi_eof(urxp->cmd), umi_qos(urxp->cmd), umi_prot(urxp->cmd),
                        umi_ex(urxp->cmd));
                    utxp->dstaddr = urxp->srcaddr;
                    utxp->srcaddr = urxp->dstaddr;

                    // try to send the response
                    if (!tx.send(txp)) {
                        // if sending the response failed, indicate that there
                        // is a response in progress
                        resp.in_progress = true;
                        resp.out_channel = &tx;
                    }
                }
            } else if (((opcode == UMI_REQ_READ) || (opcode == UMI_REQ_RDMA)) &&
                       (!resp.in_progress)) {

                // ACK
                rx.recv();

                // format the response.  EOM, LEN, and DATA are filled in
                // later in the code, and dstaddr/srcaddr are updated as
                // each response packet is sent

                uint32_t resp_opcode = (opcode == UMI_REQ_READ) ? UMI_RESP_READ : UMI_REQ_POSTED;

                utxp->cmd = umi_pack(resp_opcode, 0, size, 0, 0, umi_eof(urxp->cmd),
                    umi_qos(urxp->cmd), umi_prot(urxp->cmd), umi_ex(urxp->cmd));
                utxp->dstaddr = urxp->srcaddr;
                utxp->srcaddr = urxp->dstaddr;

                // save parameters describing the read
                resp.read_bytes_remaining = nbytes;
                resp.read_dstaddr = dstaddr;
                resp.read_size = size;
                resp.out_channel = (opcode == UMI_REQ_READ) ? (&tx) : (&req_tx);
            } else if ((opcode == UMI_REQ_ATOMIC) && (!resp.in_progress)) {
                // ACK
                rx.recv();

                // perform the atomic operation
                int64_t result = atomic_op(dstaddr, urxp->data, umi_atype(urxp->cmd), size);

                // copy result into the response packet
                if (nbytes > sizeof(utxp->data)) {
                    fprintf(stderr,
                        "***ERROR: Number of bytes in atomic transaction (%u)"
                        " exceeds UMI packet data width (%zu bytes)",
                        nbytes, sizeof(utxp->data));
                } else if (nbytes > sizeof(result)) {
                    fprintf(stderr,
                        "***ERROR: Number of bytes in atomic transaction (%u)"
                        " exceeds size of the result (%zu bytes)",
                        nbytes, sizeof(result));
                } else {
                    memcpy(utxp->data, &result, nbytes);
                }

                // format the response
                utxp->cmd = umi_pack(UMI_RESP_READ, 0, size, 0, 1, umi_eof(urxp->cmd),
                    umi_qos(urxp->cmd), umi_prot(urxp->cmd), umi_ex(urxp->cmd));
                utxp->dstaddr = urxp->srcaddr;
                utxp->srcaddr = urxp->dstaddr;

                // try to send the response
                if (!tx.send(txp)) {
                    // if sending the response fails, indicate that
                    // a packet transmission is in progress
                    resp.in_progress = true;
                    resp.out_channel = &tx;
                }
            } else if (!resp.in_progress) {
                // ACK
                rx.recv();
                fprintf(stderr, "***ERROR: Unsupported packet received (%s), skipping... \n",
                    umi_opcode_to_str(opcode).c_str());
            }
        }

        // if there's an outbound packet stuck, try to send it out
        if (resp.in_progress) {
            if (resp.out_channel->send(txp)) {
                resp.done(utxp);
            }
        }

        // try to complete a read if there is one in progress
        // note that this loop cannot run if there is an outbound
        // packet stuck, since it modifies utxp
        while ((!resp.in_progress) && (resp.read_bytes_remaining > 0)) {
            // calculate number of bytes in the next read response
            resp.flit_bytes = std::min(resp.read_bytes_remaining, (uint32_t)sizeof(utxp->data));

            // fill in fields of the UMI command.  done in a
            // somewhat verbose manner to avoid a warning about
            // taking addresses of a packed member in a structure
            uint32_t cmd = utxp->cmd;

            // fill in the LEN field.  done in a somewhat verbose
            // manner to avoid a warning about taking the address
            // of a packed member in a structure
            uint32_t len = (resp.flit_bytes >> resp.read_size) - 1;
            set_umi_len(&cmd, len);

            // fill in the EOM field, same comment about the
            // verbose style.
            uint32_t eom = (resp.flit_bytes == resp.read_bytes_remaining) ? 1 : 0;
            set_umi_eom(&cmd, eom);

            // commit changes to the UMI command
            utxp->cmd = cmd;

            // copy read data into the response packet
            if (in_range(resp.read_dstaddr, resp.flit_bytes, SRAM_BASE, SRAM_BASE_SIZE)) {
                memcpy(utxp->data, sram + (resp.read_dstaddr - SRAM_BASE), resp.flit_bytes);
            } else {
                fprintf(stderr,
                    "***ERROR: Memory read out of range: resp_dstaddr=0x%" PRIx64 ", flit_bytes=%u",
                    resp.read_dstaddr, resp.flit_bytes);
            }

            // try to send the response packet
            if (resp.out_channel->send(txp)) {
                // if that succeeds, update the state of the read transaction
                resp.done(utxp);
            } else {
                // otherwise indicate that we need to retry sending this packet
                resp.in_progress = true;
            }
        }
    }

    delete[] sram;
    return 0;
}
