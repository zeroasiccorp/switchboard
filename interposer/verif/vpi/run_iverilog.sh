#!/bin/bash

set -euf -o pipefail

iverilog-vpi zmq_vpi.c -lzmq
iverilog -o testbench_vpi.vvp -s testbench_vpi -f files.txt
vvp -M. -mzmq_vpi testbench_vpi.vvp
