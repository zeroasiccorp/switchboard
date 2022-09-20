#include "switchboard.hpp"

int main(int argc, char* argv[]) {
    int arg_idx = 1;

    std::string str = "";
    if (arg_idx < argc) {
        str = argv[arg_idx++];
    }

    umi_packet p;
    str_to_umi_packet(str, p);
    printf("%s\n", umi_packet_to_str(p).c_str());

    return 0;
}
