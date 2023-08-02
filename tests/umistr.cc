#include "umilib.hpp"

int main(int argc, char* argv[]) {
    // form UMI packet with an interesting pattern
    umi_packet p0;
    for (int i = 0; i < 8; i++) {
        p0[i] = 0;
        for (int j = 0; j < 8; j++) {
            p0[i] <<= 4;
            p0[i] |= (i + j) % 16;
        }
    }

    // convert to a string
    std::string s0 = umi_packet_to_str(p0);
    printf("p0: %s\n", umi_packet_to_str(p0).c_str());

    // convert to a packet
    umi_packet p1;
    str_to_umi_packet(s0, p1);

    // convert to a string
    std::string s1 = umi_packet_to_str(p1);
    printf("p1: %s\n", umi_packet_to_str(p1).c_str());

    // check that strings match
    assert(s0 == s1);

    // check that packets match
    for (int i = 0; i < 8; i++) {
        assert(p0[i] == p1[i]);
    }

    return 0;
}
