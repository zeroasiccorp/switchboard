#!/bin/bash

# ref: https://spin.atomicobject.com/2017/08/24/start-stop-bash-background-process/
trap "exit" INT TERM ERR
trap "kill 0" EXIT

# figure out where shared memory queues are located
UNAME_S=$(uname -s)
if [ "$UNAME_S" == "Darwin" ]; then
    SHMEM_DIR="/tmp/boost_interprocess"
else
    SHMEM_DIR="/dev/shm"
fi

# clean up old queues if present
rm -f "${SHMEM_DIR}/queue-5555"
rm -f "${SHMEM_DIR}/queue-5556"

# launch the verilator simulation as a background process
./verilator/obj_dir/Vtestbench &

# launch a client to communicate with the simulation
./cpp/client
