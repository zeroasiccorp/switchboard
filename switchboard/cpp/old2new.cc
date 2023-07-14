#include "switchboard.hpp"
#include "old_umilib.hpp"
#include "old_umisb.hpp"
#include "old_umilib.h"
#include "umilib.hpp"
#include "umisb.hpp"
#include "umilib.h"

std::vector<std::unique_ptr<SBRX>> old_rx;
std::vector<std::unique_ptr<SBTX>> old_tx;
std::vector<std::unique_ptr<SBRX>> new_req_rx;
std::vector<std::unique_ptr<SBTX>> new_req_tx;
std::vector<std::unique_ptr<SBRX>> new_resp_rx;
std::vector<std::unique_ptr<SBTX>> new_resp_tx;
int nconn = 0;

bool verbose = false;
bool should_yield = false;

volatile sig_atomic_t quit = 0;

void signal_callback_handler(int signum) {
    quit = 1;
}

void init(int argc, char* argv[]) {
    int arg_idx = 1;

    while (arg_idx < argc) {
        std::string s = std::string(argv[arg_idx++]);

        if ((s == "-v") || (s == "--verbose")) {
            verbose = true;
        } else if (s == "--should-yield") {
            should_yield = true;
        } else {
            nconn++;

            // ref: https://stackoverflow.com/a/14266139
            std::string delim = ":";
            for (int i=0; i<=5; i++) {
                size_t pos = s.find(delim);
                std::string token;
                if (pos != std::string::npos) {
                    token = s.substr(0, pos);
                    s.erase(0, pos + delim.length());
                } else {
                    token = "";
                }

                if (i == 0) {
                    // old_rx
                    old_rx.push_back(std::unique_ptr<SBRX>(new SBRX()));
                    if (token != "") {
                        old_rx.back()->init(token);
                    }
                } else if (i == 1) {
                    // old_tx
                    old_tx.push_back(std::unique_ptr<SBTX>(new SBTX()));
                    if (token != "") {
                        old_tx.back()->init(token);
                    }
                } else if (i == 2) {
                    // new_req_rx
                    new_req_rx.push_back(std::unique_ptr<SBRX>(new SBRX()));
                    if (token != "") {
                        new_req_rx.back()->init(token);
                    }
                } else if (i == 3) {
                    // new_req_tx
                    new_req_tx.push_back(std::unique_ptr<SBTX>(new SBTX()));
                    if (token != "") {
                        new_req_tx.back()->init(token);
                    }
                } else if (i == 4) {
                    // new_resp_rx
                    new_resp_rx.push_back(std::unique_ptr<SBRX>(new SBRX()));
                    if (token != "") {
                        new_resp_rx.back()->init(token);
                    }
                } else if (i == 5) {
                    // new_resp_tx
                    new_resp_tx.push_back(std::unique_ptr<SBTX>(new SBTX()));
                    if (token != "") {
                        new_resp_tx.back()->init(token);
                    }
                }
            }
        }
    }
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_callback_handler);

    // set up connections
    init(argc, argv);

    // handle incoming packets

    while (!quit) {
        bool any_received = false;

        for (int i=0; i<nconn; i++) {
            ////////////
            // old_rx //
            ////////////

            {
                OldUmiTransaction old_req_txn;

                if (old_umisb_recv(old_req_txn, *old_rx[i], false)) {
                    any_received = true;

                    if (old_is_umi_read_request(old_req_txn.opcode)) {
                        if (new_req_tx[i]->is_active() && new_resp_rx[i]->is_active() &&
                            old_tx[i]->is_active()) {
                            // create response object
                            // note the swapped srcaddr and dstaddr fields
                            OldUmiTransaction old_resp_txn(OLD_UMI_WRITE_RESPONSE, old_req_txn.size,
                                old_req_txn.user, old_req_txn.srcaddr, old_req_txn.dstaddr);
                            old_resp_txn.resize(1 << old_req_txn.size);

                            // issue new UMI read(s)
                            int nreq = 1<<old_req_txn.size;
                            int nresp = nreq;
                            uint8_t* ptr = old_resp_txn.ptr();
                            uint64_t dstaddr = old_req_txn.dstaddr;
                            uint64_t srcaddr = old_req_txn.srcaddr;
                            while ((nreq > 0) || (nresp > 0)) {
                                if (nreq > 0) {
                                    // TODO: could issue fewer reads
                                    uint32_t nbytes = std::min(nreq, 32);
                                    uint32_t eom = (nbytes == nreq) ? 1 : 0;
                                    uint32_t cmd = umi_pack(UMI_REQ_READ, 0, 0, nbytes-1, eom, 1,
                                        0, 0, 0);
                                    UmiTransaction new_req_txn(cmd, dstaddr, srcaddr);
                                    if (umisb_send(new_req_txn, *new_req_tx[i], false)) {
                                        nreq -= nbytes;
                                        dstaddr += nbytes;
                                        srcaddr += nbytes;
                                    }
                                }
                                if (nresp > 0) {
                                    uint32_t nbytes = std::min(nresp, 32);
                                    UmiTransaction new_resp_txn(0, 0, 0, ptr, nbytes);
                                    if (umisb_recv(new_resp_txn, *new_resp_rx[i], false)) {
                                        ptr += umi_len(new_resp_txn.cmd) + 1;
                                        nresp -= (umi_len(new_resp_txn.cmd) + 1);
                                    }
                                }
                            }

                            // put result in an old transaction and
                            // send that back via old_umisb_send
                            old_umisb_send(old_resp_txn, *old_tx[i]);
                        } else {
                            throw std::runtime_error("new_req_tx, new_resp_rx, and/or old_tx not active");
                        }
                    } else if (old_is_umi_atomic(old_req_txn.opcode)) {
                        if (new_req_tx[i]->is_active() && new_resp_rx[i]->is_active()
                            && old_tx[i]->is_active()) {
                            // issue new UMI atomic
                            uint32_t atype = old_req_txn.opcode >> 4;
                            uint32_t cmd = umi_pack(UMI_REQ_ATOMIC, atype, old_req_txn.size, 0, 1, 1);
                            UmiTransaction new_req_txn(cmd, old_req_txn.dstaddr, old_req_txn.srcaddr,
                                old_req_txn.ptr(), old_req_txn.nbytes());
                            umisb_send(new_req_txn, *new_req_tx[i]);

                            // get result
                            UmiTransaction new_resp_txn;
                            umisb_recv(new_resp_txn, *new_resp_rx[i]);

                            // put result in an old transaction
                            // note the swapped dstaddr and srcaddr
                            OldUmiTransaction old_resp_txn(OLD_UMI_WRITE_RESPONSE, old_req_txn.size,
                                old_req_txn.user, old_req_txn.srcaddr, old_req_txn.dstaddr,
                                new_resp_txn.ptr(), new_resp_txn.nbytes());

                            // send that back via old_umisb_send
                            old_umisb_send(old_resp_txn, *old_tx[i]);
                        } else {
                            throw std::runtime_error("new_req_tx, new_resp_rx, and/or old_tx not active");
                        }
                    } else if (old_is_umi_write_posted(old_req_txn.opcode)) {
                        // this should only be a write originating from the old block
                        if (new_req_tx[i]->is_active()) {
                            // issue new UMI posted writes(s)
                            int nreq = 1<<old_req_txn.size;
                            uint64_t dstaddr = old_req_txn.dstaddr;
                            uint64_t srcaddr = old_req_txn.srcaddr;
                            while (nreq > 0) {
                                uint32_t nbytes = std::min(nreq, 32);
                                uint32_t eom = (nbytes == nreq) ? 1 : 0;
                                uint32_t cmd = umi_pack(UMI_REQ_POSTED, 0, 0, nbytes-1, eom, 1, 0, 0, 0);
                                UmiTransaction new_req_txn(cmd, dstaddr, srcaddr,
                                    old_req_txn.ptr(), nbytes);
                                umisb_send(new_req_txn, *new_req_tx[i]);
                                nreq -= nbytes;
                                dstaddr += nbytes;
                                srcaddr += nbytes;
                            }
                        } else {
                            throw std::runtime_error("new_req_tx is not active.");
                        }
                    } else {
                        throw std::runtime_error("Unsupported command recevied on old_rx.");
                    }
                }
            }

            ////////////////
            // new_req_rx //
            ////////////////

            {
                UmiTransaction new_req_txn;

                if (umisb_recv(new_req_txn, *new_req_rx[i], false)) {
                    uint32_t opcode = umi_opcode(new_req_txn.cmd);
                    if ((opcode == UMI_REQ_WRITE) || (opcode == UMI_REQ_POSTED)) {

                        // issue old posted write(s).  this may need to be broken
                        // up into multiple writes if not a power of two
                        if (old_tx[i]->is_active()) {
                            uint32_t nreq = (umi_len(new_req_txn.cmd)+1)<<umi_size(new_req_txn.cmd);
                            uint64_t dstaddr = new_req_txn.dstaddr;
                            uint64_t srcaddr = new_req_txn.srcaddr;
                            uint8_t* ptr = new_req_txn.ptr();
                            int pow2 = 0;
                            while (nreq > 0) {
                                int nbytes = 1 << pow2;
                                if ((nreq >> pow2) & 1) {
                                    // even if the opcode is UMI_REQ_WRITE, use an old posted
                                    // write, since old UMI HW did not implement ack'd writes
                                    OldUmiTransaction old_req_txn(OLD_UMI_WRITE_POSTED, pow2,
                                        0, dstaddr, srcaddr, ptr, nbytes);
                                    
                                    old_umisb_send(old_req_txn, *old_tx[i]);
                                    nreq -= nbytes;
                                    dstaddr += nbytes;
                                    srcaddr += nbytes;
                                }
                                pow2++;
                            }
                            // send back a write response if needed
                            // note the swapped srcaddr and dstaddr
                            uint32_t cmd = umi_pack(UMI_RESP_WRITE, 0, umi_size(new_req_txn.cmd),
                                umi_len(new_req_txn.cmd), 1, 1);
                            UmiTransaction umi_resp_txn(cmd, new_req_txn.srcaddr, new_req_txn.dstaddr);
                            if (new_resp_tx[i]->is_active()) {
                                umisb_send(umi_resp_txn, *new_resp_tx[i]);
                            } else {
                                throw std::runtime_error("new_resp_tx is not active");
                            }
                        } else {
                            throw std::runtime_error("old_tx is not active");
                        }
                    } else if (opcode == UMI_REQ_READ) {
                        // issue old read(s).  this may need to be broken up
                        // into multiple reads if not a power of two

                        if (old_tx[i]->is_active() && old_rx[i]->is_active() && new_resp_tx[i]->is_active()) {
                            // issue old reads to get the data
                            int old_nreq = (umi_len(new_req_txn.cmd)+1)<<umi_size(new_req_txn.cmd);
                            int old_nresp = old_nreq;
                            int new_nresp = old_nreq;
                            uint8_t* data = new uint8_t[old_nreq];  // max size is 32k
                            uint64_t old_dstaddr = new_req_txn.dstaddr;
                            uint64_t old_srcaddr = new_req_txn.srcaddr;
                            uint64_t new_dstaddr = new_req_txn.dstaddr;
                            uint64_t new_srcaddr = new_req_txn.srcaddr;
                            uint8_t* ptr = new_req_txn.ptr();
                            int pow2 = 0;
                            while ((old_nreq > 0) || (old_nresp > 0)) {
                                if (old_nreq > 0) {
                                    int nbytes = 1 << pow2;
                                    if ((old_nreq >> pow2) & 1) {
                                        // issue an old read request
                                        OldUmiTransaction old_req_txn(OLD_UMI_READ_REQUEST, pow2,
                                            0, old_dstaddr, old_srcaddr);
                                        if (old_umisb_send(old_req_txn, *old_tx[i], false)) {
                                            old_nreq -= nbytes;
                                            old_dstaddr += nbytes;
                                            old_srcaddr += nbytes;
                                        }
                                    }
                                    pow2++;
                                }
                                if (old_nresp > 0) {
                                    // get old read response
                                    OldUmiTransaction old_resp_txn(0, 0, 0, 0, 0, data, old_nresp);
                                    if (old_umisb_recv(old_resp_txn, *old_rx[i], false)) {
                                        old_nresp -= old_resp_txn.nbytes();
                                    }
                                }
                            }

                            // send out the data using new read responses
                            while (new_nresp > 0) {
                                int nbytes = std::min(new_nresp, 32);
                                uint32_t eom = (nbytes == new_nresp) ? 1 : 0;
                                uint32_t cmd = umi_pack(UMI_RESP_READ, 0, umi_size(new_req_txn.cmd),
                                    (nbytes >> umi_size(new_req_txn.cmd)) - 1, eom, 1, 0);
                                // note the swapped srcaddr and dstaddr
                                UmiTransaction new_resp_txn(cmd, new_srcaddr, new_dstaddr, data, nbytes);
                                umisb_send(new_resp_txn, *new_resp_tx[i]);
                                new_nresp -= nbytes;
                                new_dstaddr += nbytes;
                                new_srcaddr += nbytes;
                            }

                            // delete the data buffer now that we're done with it
                            delete[] data;
                        } else {
                            throw std::runtime_error("old_tx, old_rx, and/or new_resp_tx is not active.");
                        }
                    } else if (opcode == UMI_REQ_ATOMIC) {
                        if (old_tx[i]->is_active() && old_rx[i]->is_active()
                            && new_resp_tx[i]->is_active()) {
                            // issue an old UMI atomic request
                            uint32_t opcode = ((umi_atype(new_req_txn.cmd) & 0xf) << 4) | 0x4;
                            OldUmiTransaction old_req_txn(opcode, umi_size(new_req_txn.cmd),
                                0, new_req_txn.dstaddr, new_req_txn.srcaddr, new_req_txn.ptr(),
                                new_req_txn.nbytes());
                            old_umisb_send(old_req_txn, *old_tx[i]);

                            // get old UMI atomic response
                            OldUmiTransaction old_resp_txn;
                            old_umisb_recv(old_resp_txn, *old_rx[i]);

                            // send as a new UMI atomic response
                            // note the swapped dstaddr and srcaddr
                            // TODO what is the right opcode to use?
                            uint32_t cmd = umi_pack(UMI_RESP_READ, 0, umi_size(new_req_txn.cmd), 0, 1, 1);
                            UmiTransaction new_resp_txn(cmd, new_req_txn.srcaddr,
                                new_req_txn.dstaddr, old_resp_txn.ptr(), old_resp_txn.nbytes());
                            umisb_send(new_resp_txn, *new_resp_tx[i]);
                        } else {
                            throw std::runtime_error("old_tx, old_rx, and/or new_resp_tx is not active.");
                        }
                    } else {
                        throw std::runtime_error("Unsupported command recevied on new_req_rx.");
                    }
                }
            }

        }

        // yield if needed
        if (should_yield && (!any_received)) {
            std::this_thread::yield();
        }
    }

    return 0;
}
