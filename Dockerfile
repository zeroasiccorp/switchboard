# Docker container for emulation testing
# Copyright (C) 2023 Zero ASIC

FROM ubuntu:22.04

# basic setup, including Python and Node.js installations
# (Node.js is needed for some GitHub Actions)
RUN \
apt update -y && \
apt install -y curl unzip libsystemc libsystemc-dev \
    python3 python3-dev python3-pip && \
python3 -m pip install --upgrade pip && \
curl -fsSL https://deb.nodesource.com/setup_19.x | bash - && \
apt install -y nodejs && \
apt clean && \
rm -rf /var/lib/apt/lists/*

# install Verilator.  the final remove in the same RUN command
# is important to keep the docker image size low
# https://verilator.org/guide/latest/install.html#git-quick-install
RUN \
apt update -y && \
apt install -y git perl python3 make autoconf g++ flex bison \
    ccache libgoogle-perftools-dev numactl perl-doc && \
apt install -y libfl2 && \
apt install -y libfl-dev && \
git clone https://github.com/verilator/verilator && \
cd verilator && \
git pull && \
git checkout v5.004 && \
autoconf && \
./configure && \
make -j `nproc` && \
make install && \
cd .. && \
rm -rf verilator && \
apt clean && \
rm -rf /var/lib/apt/lists/*

# install Icarus Verilog.  the final remove in the same RUN command
# is important to keep the docker image size low
# https://iverilog.fandom.com/wiki/Installation_Guide#Obtaining_Source_From_git
RUN \
apt update -y && \
apt install -y autoconf gperf && \
git clone https://github.com/steveicarus/iverilog.git && \
cd iverilog && \
git checkout --track -b v11-branch origin/v11-branch && \
sh autoconf.sh && \
./configure && \
make -j `nproc` && \
make install && \
cd .. && \
rm -rf iverilog && \
apt clean && \
rm -rf /var/lib/apt/lists/*

# install RISC-V toolchain.  the final remove in the same RUN command
# is important to keep the docker image size low (particularly true
# for this package, where the build consumes several GB)
# https://github.com/riscv-collab/riscv-gnu-toolchain
RUN \
apt update -y && \
apt install -y autoconf automake autotools-dev curl python3 \
    libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex \
    texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build && \
git clone https://github.com/riscv/riscv-gnu-toolchain && \
cd riscv-gnu-toolchain && \
git pull && \
git checkout 2023.01.04 && \
./configure --prefix=/opt/riscv && \
make -j `nproc` && \
cd .. && \
rm -rf riscv-gnu-toolchain && \
apt clean && \
rm -rf /var/lib/apt/lists/*

# set environment
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/riscv/bin
