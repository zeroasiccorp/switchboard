#!/bin/bash

set -euf -o pipefail

mkdir -p deps
cd deps

git clone git@github.com:Xilinx/libsystemctlm-soc.git
cd libsystemctlm-soc && git checkout 670d73c && cd ..

git clone git@github.com:zeroasiccorp/umi.git
cd umi && git checkout 1fce4fc && cd ..

cd ..
