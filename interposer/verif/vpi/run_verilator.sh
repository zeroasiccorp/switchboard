#!/bin/bash

set -euf -o pipefail

mkdir -p obj_dir
gcc -I/usr/local/Cellar/verilator/4.222/share/verilator/include/vltstd \
    -fPIC -shared -Wl,-undefined,dynamic_lookup -o obj_dir/libvpi.so
verilator --cc --exe --vpi --no-l2name obj_dir/libvpi.so testbench.cc ../verilator/config.vlt -f files.txt --top testbench_vpi
