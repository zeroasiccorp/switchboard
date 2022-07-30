#!/bin/bash

# cause exit command to run if we get SIGINT or SIGTERM,
# which in turn will trigger EXIT.  this is needed to make
# sure that the simulator background process is killed, since
# otherwise, it can be quite annoying to clean up.

# ref: https://spin.atomicobject.com/2017/08/24/start-stop-bash-background-process/

trap "exit" INT TERM ERR

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

# launch the verilator simulation as a background process,
# and add a trap that will kill the process on exit
./verilator/obj_dir/Vtestbench &
VERILATOR_PID=$!
trap "kill ${VERILATOR_PID}" EXIT

# launch a client to communicate with the simulation
./cpp/client
