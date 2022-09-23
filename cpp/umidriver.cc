#include <cstddef>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <unistd.h>
#include <fstream>
#include <signal.h>
#include <sys/wait.h>

#include "switchboard.hpp"
#include "umilib.hpp"

int main(int argc, char* argv[]) {
    // process command-line arguments

    std::string sim = "-";
    std::string txfile = "-";
    std::string rxfile = "-";
    std::string outfile = "out.memh";
    std::string txqueue = "queue-5556";
    std::string rxqueue = "queue-5555";

    int arg_idx = 1;
    while (arg_idx < (argc-1)) {
        std::string key = argv[arg_idx++];
        std::string val = argv[arg_idx++];
        if (key == "--sim") {
            sim = val;
        } else if (key == "--txfile") {
            txfile = val;
        } else if (key == "--rxfile") {
            rxfile = val;
        } else if (key == "--outfile") {
            outfile = val;
        } else if (key == "--txqueue") {
            txqueue = val;
        } else if (key == "--rxqueue") {
            rxqueue = val;
        }
    }

    // determine the name of the TX queue, and clean up an
    // old version of the queue, if present
    if (txqueue != "-") {
        delete_shared_queue(txqueue);
    }

    // determine the name of the RX queue, and clean up an
    // old version of the queue, if present
    if (rxqueue != "-") {
        delete_shared_queue(rxqueue);
    }

    int pid = fork();
    int correct_count = 0;
    int incorrect_count = 0;

    if (pid == 0) {
        // child, should run the simulator executable
        if (sim != "-") {
            // build up the argument list

            std::vector<std::string> arr;

            //arr.push_back("verilator");
            arr.push_back(sim);
            if (txqueue != "-") {
                arr.push_back("+tx_port=" + txqueue);
            }
            if (rxqueue != "-") {
                arr.push_back("+rx_port=" + rxqueue);
            }

            // convert the argument list to c-strings, with
            // the final argument being "NULL"

            std::vector<char*> arr_as_cstrs;
            for (auto & elem : arr) {
                arr_as_cstrs.push_back((char*)(elem.c_str()));
            }
            arr_as_cstrs.push_back(nullptr);

            // launch the simulator process
            execv(sim.c_str(), arr_as_cstrs.data());
        }
    } else {
        // initialize driver's TX connection (which is connected to the DUT's RX port)
        SBTX tx;
        if (rxqueue != "-") {
            tx.init(rxqueue);
        }

        // initialize driver's RX connection (which is connected to the DUT's TX port)
        SBRX rx;
        if (txqueue != "-") {
            rx.init(txqueue);
        }

        // open file of tx transactions
        bool txeof = false;
        bool txvalid = false;
        sb_packet txp;
        std::ifstream txstream;
        if (txfile != "-") {
            txstream.open(txfile);
        } else {
            txeof = true;
        }

        // open file of rx transactions
        bool rxeof = false;
        bool rxvalid = false;
        sb_packet rxp;
        std::ifstream rxstream;
        if (rxfile != "-") {
            rxstream.open(rxfile);
        } else {
            rxeof = true;
        }

        // open file that will store received UMI transactions
        std::ofstream outstream;
        if (outfile != "-") {
            outstream.open(outfile);
        }

        int rxline = 0;
        while (txvalid || rxvalid || (!txeof) || (!rxeof)) {
            // boolean variables used to determine if we should back off
            bool tx_votes_to_yield = false;
            bool rx_votes_to_yield = false;

            // read the next TX packet
            while ((!txvalid) && (!txeof)) {
                std::string line;
                if (std::getline(txstream, line)) {
                    txvalid = str_to_umi_packet(line, (uint32_t*)txp.data);
                    if (!txvalid) {
                        printf("txfile: skipping line \"%s\"\n", line.c_str());
                    } else { 
                        txp.destination = 0;  // TODO: populate from address
                        txp.last = 0;
                    }
                } else {
                    txeof = true;
                }
            }

            // if there is a valid packet, try to send it
            // if sending is successful, mark the current
            // TX packet as invalid so it will not be
            // sent again
            if (txvalid && tx.is_active()) {
                if (tx.send(txp)) {
                    txvalid = false;
                } else {
                    // we should back off in this case, since the are
                    // TX packets to be sent, but the queue is full
                    tx_votes_to_yield = true;
                }
            }

            // read the next RX packet from file
            while ((!rxvalid) && (!rxeof)) {
                // increment line counter to match current line in the RX file
                rxline++;

                // read line
                std::string line;
                if (std::getline(rxstream, line)) {
                    rxvalid = str_to_umi_packet(line, (uint32_t*)rxp.data);
                    if (!rxvalid) {
                        printf("rxfile: skipping line \"%s\"\n", line.c_str());
                    }
                } else {
                    rxeof = true;
                }
            }

            // try to read the next RX packet from simulation
            if (rx.is_active()) {
                sb_packet outp;
                if (rx.recv(outp)) {
                    // write to output file, if active
                    if (outstream.is_open()) {
                        outstream << umi_packet_to_str((uint32_t*)outp.data) << std::endl;
                    }

                    // if there's an expected RX packet, check against it
                    if (rxvalid) {
                        if (!umi_packets_match((uint32_t*)outp.data, (uint32_t*)rxp.data)) {
                            // if there's an error, print out what it is, and
                            // increment the error counter
                            printf("*** mismatch at rxfile line %d ***\n", rxline);
                            printf("got:      %s\n", umi_packet_to_str((uint32_t*)outp.data).c_str());
                            printf("expected: %s\n", umi_packet_to_str((uint32_t*)rxp.data).c_str());
                            incorrect_count++;
                        } else {
                            correct_count++;
                        }

                        // in any case, mark rxp as invalid, since we just checked against it
                        // this will cause the next expected packet to be read from file on the
                        // next iteration
                        rxvalid = false;
                    }
                } else {
                    if (rxvalid) {
                        // we should back off in this case, since we are expecting to receive
                        // a packet, but haven't received it
                        rx_votes_to_yield = true;
                    }
                }
            }

            // back off if necessary
            if (tx_votes_to_yield && rx_votes_to_yield) {
                std::this_thread::yield();
            }
        }

        // send SIGINT to simulator and wait for it to exit
        kill(pid, SIGINT);
        wait(NULL);

        // print a summary of the test
        printf("*** summary ***\n");
        printf("#   correct: %d\n", correct_count);
        printf("# incorrect: %d\n", incorrect_count);
    }

    if (incorrect_count > 0) {
        // return non-zero code to indicate there were some errors
        return 1;
    } else {
        return 0;
    }
}
